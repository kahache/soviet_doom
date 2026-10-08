#!/usr/bin/env python3
"""Build the mod PK3 from src/ (stdlib only).

Usage:
  python3 tools/build.py                 # -> dist/sovietdoom.pk3
  python3 tools/build.py --out other.pk3
  python3 tools/build.py --print-textmap MAP01   # show generated UDMF

Nothing is added to the PK3 by hand: everything comes from src/ (see
docs/engine/MOD-SPEC.md for the layout contract).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TOOLS_DIR.parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from sdbuild.pk3 import BuildError, build  # noqa: E402
from sdbuild.wad import read_lump  # noqa: E402

MOD_NAME = "sovietdoom"  # provisional; the CEO decides the final name (D1)
DEFAULT_SRC = PROJECT_ROOT / "src"
DEFAULT_OUT = PROJECT_ROOT / "dist" / f"{MOD_NAME}.pk3"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--src", type=Path, default=DEFAULT_SRC, help="source tree (default: src/)")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="output .pk3 (default: dist/%s.pk3)" % MOD_NAME)
    parser.add_argument("--quiet", action="store_true", help="only print errors")
    parser.add_argument("--print-textmap", metavar="MAP", help="print the generated TEXTMAP of MAP and exit")
    args = parser.parse_args(argv)

    try:
        entries = build(args.src, args.out, TOOLS_DIR)
    except BuildError as exc:
        print(f"build error: {exc}", file=sys.stderr)
        return 1

    if args.print_textmap:
        wanted = f"maps/{args.print_textmap.upper()}.wad"
        for e in entries:
            if e.path.lower() == wanted.lower():
                sys.stdout.write(read_lump(e.data, "TEXTMAP").decode("ascii"))
                return 0
        print(f"build error: no map {args.print_textmap} in PK3", file=sys.stderr)
        return 1

    if not args.quiet:
        total = sum(len(e.data) for e in entries)
        print(f"{args.out} ({len(entries)} files, {total} bytes uncompressed)")
        for e in entries:
            print(f"  {e.path:<32} {len(e.data):>8}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
