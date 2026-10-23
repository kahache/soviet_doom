#!/usr/bin/env python3
"""Which tests run at which `tools/verify.py` tier, and the runner that applies it.

    python tests/_tiers.py fast               # what `verify.py fast` runs
    python tests/_tiers.py art                # the whole suite (art and full)
    python tests/_tiers.py --list             # the split, counted, run nothing
    python tests/_tiers.py fast --durations 15   # name the slowest tests

Why this file exists: by 2026-10-14 the suite had grown to ~1600 tests and
`verify.py fast`, the loop every agent runs several times per task, took
~100 s instead of the ~6 s it was built for. A handful of classes paid most
of it: one test that globs work/ once per installed PNG (26 s), route data
built from both maps (9 s), the release built end to end, and every art
generator rendering its sheets. None of them is needed to know whether an
edit broke the package; all of them are needed before a phase closes.

The rule, one sentence: `fast` is the build, check_pk3 and every test that
reads text or a small file; a test that RENDERS art, reads gzdoom.pk3, packs
a release or an overlay, scans work/ or builds route/map geometry runs at
`art` and `full` instead. Nothing is lost: `art` runs EVERY test discovered
(the SLOW entries below plus everything `fast` runs), and `--list` proves
the arithmetic (fast + art-only = discovered).

How a test moves tier WITHOUT touching its file: add its test-id prefix to
SLOW below (a module, a `module.Class` or a `module.Class.test_name`), with
the reason. The test files belong to other agents; this table is QA's.
The older switch, `SD_SKIP_SLOW_ART=1` (set by verify.py at `fast`), still
works inside the files that read it; this table is for the ones that do not.

A shared build cache. Nineteen tests built the same PK3 from the same tree,
~0.4 s each. The runner wraps `sdbuild.pk3.build` before discovery, so a
second build of an identical tree copies the first one's bytes instead of
zipping again. The key is the resolved src/assets/tools paths plus a
SHA-256 of every file's path and CONTENT under src/, assets/ and the tools
tree (bytecode excluded), so any edit, even mid-run, misses the cache. A
file is re-read whenever its size or mtime moves (an unchanged file's
digest is remembered, which makes a key ~0.1 s instead of ~0.3 s). It
lives for one process (one unittest session), never on disk. It is
bypassed for the builder's own tests (BUILD_CACHE_BYPASS): reproducibility
of the zip is what tests/test_build.py checks, and a cache would make that
check vacuous. `python -m unittest discover -s tests` (CI, coverage.sh)
does not go through this file and builds every time, as before.

Standard library only, like everything in tools/.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_DIR.parent
TOOLS_DIR = PROJECT_ROOT / "tools"

TIERS = ("fast", "art")

# --- The table -------------------------------------------------------------
# (test-id prefix, why it is not in `fast`). A prefix matches a test whose
# id equals it or starts with it plus a dot. Kept sorted by module. Measured
# 2026-10-14 on the Windows PC, single process, build cache on; the seconds
# are the class's wall time including setUpClass.
#
# Categories, so a reader can check an entry against the rule:
#   render    runs an art/sound generator or the rig and inspects pixels/samples
#   work/     walks the gitignored work/ tree file by file
#   release   builds a release (PK3 + credits + registers) end to end
#   overlay   packs a draft overlay PK3 from work/
#   geometry  builds map/route geometry (sight lines, reach, walks)
#   engine    reads the installed gzdoom.pk3 or fakes an engine run/timeout
#   package   builds the PK3 and runs check_pk3 over all of it again
SLOW: tuple[tuple[str, str], ...] = (
    ("test_art.ApprovedAssetsTests.test_identical_to_work_source",
     "work/: one rglob of work/ per installed PNG, 26 s alone"),
    ("test_art.Batch1Tests", "render: regenerates every batch-1 texture"),
    ("test_art.EmblemGeometryTests", "render: draws the emblem"),
    ("test_audition", "work/: its module fixtures hash all of work/audio (296 MB) twice, ~3 s"),
    ("test_cov_art_previews.ContactSheetTests", "render: contact sheets"),
    ("test_cov_art_previews.EmblemCheckTests", "render: emblem panels, 2.5 s"),
    ("test_cov_gen_menu.BuildFontTests", "render: builds the menu font"),
    ("test_cov_gen_menu.DefaultPathsAreResolvedAtCallTimeTests",
     "render: whole font builds, 1.7 s"),
    ("test_cov_gen_menu.SheetTests", "render: font sheets, 1.4 s"),
    ("test_cov_gen_switch.ApprovedSwitchTests", "render: regenerates the approved switches"),
    ("test_cov_gen_switch.MeasureTests", "render: every switch variant, off and on"),
    ("test_cov_gen_switch.VariantStateTests", "render: every switch variant, several times"),
    ("test_draft_overlay", "overlay: packs the draft-sprite overlay from work/, 2.4 s"),
    ("test_gen_cursor.BuildTests", "render: builds the cursor set, 1.4 s"),
    ("test_gen_enemy.SpriteTests", "render: enemy sprites"),
    ("test_gen_font.MetricsTests", "render: glyphs, to measure them"),
    ("test_gen_font.PenRuleTests", "render: glyphs per style and size"),
    ("test_gen_font.ReproductionTests", "render: builds the font twice, 1.4 s"),
    ("test_gen_font.SheetsAndCliTests", "render: font sheets, 1.4 s"),
    ("test_gen_font_fix.FontInfNewlineTests", "render: builds font variant C"),
    ("test_gen_font_fix.ProposalBuildTests", "render: builds the proposal font, 0.9 s"),
    ("test_gen_font_umlaut.GermanOutputTests", "render: builds the German glyphs"),
    ("test_gen_font_umlaut.ShippedGlyphsAreUntouchedTests", "render: three font builds, 1.2 s"),
    ("test_gen_legion.BloodTests", "render: rig blood, 1.4 s"),
    ("test_gen_legion.FullSetTests", "render: the Legion's full set"),
    ("test_gen_menu.BuildReproducesInstallTests", "render: builds the menu font"),
    ("test_gen_metro.FillDraftTests", "render: metro --fill drafts"),
    ("test_gen_metro.PaletteV2ProposalTests", "render: metro textures and sheet"),
    ("test_gen_pickups.PickupTests", "render: every pickup option and frame, 1.2 s"),
    ("test_gen_rig.BloodTests", "render: rig blood, 2.3 s"),
    ("test_gen_rig.FlatCorpseTests", "render: rig corpses, 2.8 s"),
    ("test_gen_sfx.SyntheticTest", "render: synthesises the sounds, 1.0 s"),
    ("test_gen_stalin.PipelineTests", "render: the poster sweep, 1.7 s"),
    ("test_gen_stalin.RealPhotographTests", "render: the portrait from the photograph"),
    ("test_gen_stalin.SloganTests", "render: every slogan mask"),
    ("test_gen_storm.FullSetCheapTests", "render: the Stormtrooper's set, 1.6 s"),
    ("test_gen_weapon.HandTests", "render: hand frames, 1.2 s"),
    ("test_gen_weapon.IceAxeTests", "render: ice-axe frames, 1.5 s"),
    ("test_gen_weapon.PpshTests", "render: PPSh frames, 1.0 s"),
    ("test_gen_weapon_sfx.FastRenderTest", "render: weapon sounds, twice"),
    ("test_gen_weapon_sfx.Pk3Test", "render: sound preview and compare pages, 3.0 s"),
    ("test_generators.LeninPosterTests", "render: the Lenin poster"),
    ("test_generators.SovietBaseTextureTests", "render: every base texture"),
    ("test_hand_study.HandStudyTest.test_tt33_on_freedoom_hands_at_pisg_height_and_centred",
     "render: the TT-33 on the IWAD's hands (the D61 set, retired by D123), 4.3 s alone"),
    ("test_ppsh_sprites.FileTests.test_a_fresh_build_reproduces_them",
     "render: gemini_frames rebuilds the PPSh-41 from the Gemini pair (work/ only)"),
    ("test_gemini_weapons_install.FileTests.test_a_fresh_build_reproduces_them",
     "render: gemini_frames rebuilds the IZh-58, RPG-7, ROKS-3 and hand Katyusha, ~55 s (work/ only)"),
    ("test_gemini_frames.FreshBuildTests",
     "render: gemini_frames builds the six D79-method weapons (the TT-33 since D111) from their Gemini images, ~40 s (work/ only)"),
    ("test_gemini_frames.GeneratedFramesTests",
     "work/: reads the hand_G drafts of the six D79-method weapons (the TT-33 since D111)"),
    ("test_hound_sprites.PackageTests",
     "package: builds the PK3 and runs check_pk3 on all of it again"),
    ("test_legion_sprites.PackageTests",
     "package: builds the PK3 and runs check_pk3 on all of it again"),
    ("test_map01.Map01V3Test", "geometry: sight lines and reach on MAP01, 2.8 s"),
    ("test_range_map.RangeMapTest", "geometry: sight lines on the range (RANGE), 1.1 s"),
    ("test_palette_v2.ApprovedAssetsStayInTheirVersionTests",
     "render: opens every installed PNG and counts its colours"),
    ("test_pause_sign.EngineNamesTest", "engine: reads the installed gzdoom.pk3's ZScript"),
    ("test_release.EndToEndRefusalTest", "release: packs release trees end to end, 4.3 s"),
    ("test_release.RealReleaseTest", "release: the real release, 4.1 s"),
    ("test_release_portable.RealPortableTest",
     "release: the real release plus the installed GZDoom, zipped twice (~66 MB)"),
    ("test_rifleman_sprites.PackageTests",
     "package: builds the PK3 and runs check_pk3 on all of it again"),
    ("test_route.ParseTest", "geometry: route.MapData for MAP01 and RANGE in setUpClass, 9 s"),
    ("test_smoke.TimeoutTests", "engine: waits out a hanging fake engine"),
    ("test_storm_sprites.PackageTests",
     "package: builds the PK3 and runs check_pk3 on all of it again"),
    ("test_weapon_sprites.PackageTests",
     "package: builds the PK3 and runs check_pk3 on all of it again"),
)

# Modules whose tests build the PK3 on purpose and must never get a cached one.
BUILD_CACHE_BYPASS = frozenset({"test_build"})


def matches(test_id: str, prefix: str) -> bool:
    return test_id == prefix or test_id.startswith(prefix + ".")


def is_slow(test_id: str, table=SLOW) -> bool:
    return any(matches(test_id, prefix) for prefix, _why in table)


# --- Discovery and selection -----------------------------------------------

def iter_tests(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from iter_tests(item)
        else:
            yield item


def discover() -> list[unittest.TestCase]:
    """Exactly what `python -m unittest discover -s tests` loads, flattened in
    the same order (setUpClass/setUpModule still run once per class/module:
    TestSuite tracks the previous class across a flat list)."""
    return list(iter_tests(unittest.defaultTestLoader.discover(str(TESTS_DIR))))


def select(tests, tier: str, table=SLOW) -> list[unittest.TestCase]:
    if tier == "art":
        return list(tests)
    return [t for t in tests if not is_slow(t.id(), table)]


def stale_entries(tests, table=SLOW) -> list[str]:
    """Table entries that match no discovered test: a rename sends a slow
    class back to `fast` silently unless someone says so."""
    ids = [t.id() for t in tests]
    return [prefix for prefix, _why in table if not any(matches(i, prefix) for i in ids)]


# --- The build cache ---------------------------------------------------------

def _walk(root: str):
    """Every file under root, bytecode excluded, as (path, stat)."""
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d != "__pycache__")
        for name in sorted(filenames):
            if not name.endswith(".pyc"):
                path = os.path.join(dirpath, name)
                yield path, os.stat(path)


def _called_from_bypassed_module() -> bool:
    frame = sys._getframe(2)
    while frame is not None:
        if frame.f_globals.get("__name__") in BUILD_CACHE_BYPASS:
            return True
        frame = frame.f_back
    return False


class BuildCache:
    """One process's PK3 builds, keyed by the content of what they read."""

    def __init__(self):
        self.store: dict[str, tuple[list, bytes]] = {}
        # path -> (size, mtime_ns, sha256 of the bytes). A file is read and
        # hashed again whenever its size or mtime moves, so the key follows
        # the CONTENT; an unchanged file is not re-read for every build.
        self.file_digests: dict[str, tuple[int, int, bytes]] = {}
        self.hits = 0
        self.misses = 0
        self.bypassed = 0

    def _file_digest(self, path: str, st) -> bytes:
        known = self.file_digests.get(path)
        if known and known[0] == st.st_size and known[1] == st.st_mtime_ns:
            return known[2]
        with open(path, "rb") as fh:
            digest = hashlib.sha256(fh.read()).digest()
        self.file_digests[path] = (st.st_size, st.st_mtime_ns, digest)
        return digest

    def key(self, src, tools_dir, assets) -> str:
        """src/, assets/ and the tools tree (map.py scripts import from it)."""
        h = hashlib.sha256()
        for root in (src, assets, tools_dir):
            if root is None:
                h.update(b"<none>\0")
                continue
            root = os.path.abspath(root)
            h.update(root.encode() + b"\0")
            for path, st in _walk(root):
                h.update(os.path.relpath(path, root).replace(os.sep, "/").encode() + b"\0")
                h.update(self._file_digest(path, st))
        return h.hexdigest()

    def wrap(self, original):
        def build(src, out, tools_dir, assets=None):
            if _called_from_bypassed_module():
                self.bypassed += 1
                return original(src, out, tools_dir, assets)
            key = self.key(src, tools_dir, assets)
            hit = self.store.get(key)
            if hit is None:
                self.misses += 1
                entries = original(src, out, tools_dir, assets)
                self.store[key] = (list(entries), Path(out).read_bytes())
                return entries
            self.hits += 1
            entries, data = hit
            out = Path(out)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(data)
            return list(entries)  # Entry is a frozen dataclass; the list is fresh
        build.__wrapped__ = original
        build.__doc__ = original.__doc__
        return build


def install_build_cache() -> BuildCache | None:
    if str(TOOLS_DIR) not in sys.path:
        sys.path.insert(0, str(TOOLS_DIR))
    try:
        import sdbuild.pk3 as pk3
    except ImportError:
        return None
    cache = BuildCache()
    pk3.build = cache.wrap(pk3.build)
    return cache


# --- CLI ---------------------------------------------------------------------

def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="tests/_tiers.py", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("tier", nargs="?", choices=TIERS, default="fast")
    parser.add_argument("--list", action="store_true",
                        help="count the tests per tier and print the table; run nothing")
    parser.add_argument("--no-cache", action="store_true",
                        help="build the PK3 every time, as plain unittest does")
    parser.add_argument("--durations", type=int, metavar="N",
                        help="print the N slowest tests (Python 3.12+)")
    parser.add_argument("-v", "--verbose", action="store_true")
    return parser.parse_args(argv)


def print_split(tests) -> None:
    fast = select(tests, "fast")
    art_only = [t for t in tests if is_slow(t.id())]
    print(f"discovered      {len(tests)}")
    print(f"fast            {len(fast)}")
    print(f"art only        {len(art_only)}   (SLOW table, {len(SLOW)} entries)")
    print(f"fast + art only {len(fast) + len(art_only)}   "
          f"{'== discovered' if len(fast) + len(art_only) == len(tests) else '!= discovered: BUG'}")
    print(f"art (and full)  {len(select(tests, 'art'))}   (every discovered test)")
    for prefix, why in SLOW:
        n = sum(1 for t in tests if matches(t.id(), prefix))
        print(f"  {n:4d}  {prefix:<58} {why}")


def main(argv=None) -> int:
    args = parse_args(argv)
    # The older in-file switch follows the tier, as verify.py sets it, so a
    # direct `python tests/_tiers.py fast` runs exactly what `verify.py fast` runs.
    if not args.list:
        if args.tier == "fast":
            os.environ["SD_SKIP_SLOW_ART"] = "1"
        else:
            os.environ.pop("SD_SKIP_SLOW_ART", None)
    cache = None if (args.no_cache or args.list) else install_build_cache()
    tests = discover()
    stale = stale_entries(tests)
    if args.list:
        print_split(tests)
        for prefix in stale:
            print(f"STALE: {prefix} matches no test")
        return 0

    chosen = select(tests, args.tier)
    print(f"tier {args.tier}: {len(chosen)} of {len(tests)} tests"
          + (f" ({len(tests) - len(chosen)} deferred to art: tests/_tiers.py SLOW)"
             if len(chosen) < len(tests) else ""))
    for prefix in stale:
        print(f"WARNING: tests/_tiers.py SLOW entry '{prefix}' matches no test")
    sys.stdout.flush()

    kwargs = {"verbosity": 2 if args.verbose else 1}
    if args.durations is not None and sys.version_info >= (3, 12):
        kwargs["durations"] = args.durations
    result = unittest.TextTestRunner(**kwargs).run(unittest.TestSuite(chosen))
    if cache is not None:
        print(f"build cache: {cache.misses} built, {cache.hits} reused, "
              f"{cache.bypassed} bypassed ({', '.join(sorted(BUILD_CACHE_BYPASS))})",
              file=sys.stderr)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
