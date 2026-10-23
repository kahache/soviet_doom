"""GZDoom g4.14.2 refuses an override that repeats an access qualifier.

The engine log said, for the V3 status screen: "Attempt to change
private/protected qualifiers for virtual function initShowNextLoc", and the
whole mod failed to load. An override inherits the qualifier of the virtual
it overrides, so `protected override` / `private override` must not appear.
"""
import re
import unittest
from pathlib import Path

ZSCRIPT_DIR = Path(__file__).resolve().parent.parent / "src" / "zscript"
QUALIFIED_OVERRIDE = re.compile(r"\b(?:protected|private)\s+override\b")


class OverrideQualifierTest(unittest.TestCase):
    def test_no_override_repeats_an_access_qualifier(self):
        offenders = []
        for path in sorted(ZSCRIPT_DIR.rglob("*.zs")):
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if QUALIFIED_OVERRIDE.search(line):
                    offenders.append(f"{path.relative_to(ZSCRIPT_DIR)}:{number}")
        self.assertEqual(offenders, [], "drop the qualifier: " + ", ".join(offenders))


if __name__ == "__main__":
    unittest.main()
