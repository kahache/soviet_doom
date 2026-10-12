"""Contract checks for .github/workflows/ci.yml (no GitHub Actions runner,
no PyYAML: this only has to run on bare python3, same as everything else in
this suite, including inside the CI job it is describing).

What it guards, and why each guard exists:

- The three verification commands run, in that exact order, so a failure in
  an earlier one stops the later ones from masking it (docs/PIPELINE.md,
  stage 5: "fallando a la primera").
- The built PK3 is uploaded as a run artifact.
- tools/smoke.py is never invoked here: there is no GZDoom and no IWAD on
  the runner, and the workflow must say so out loud rather than silently
  skip it, so nobody mistakes "CI is green" for "the engine loads it".
- The repo-hygiene step actually encodes a .wad/.pk3 check and a byte-size
  check, not just a comment claiming one exists.

Run:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = PROJECT_ROOT / ".github" / "workflows" / "ci.yml"

FIVE_MB = 5 * 1024 * 1024


class WorkflowFileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not WORKFLOW_PATH.is_file():
            raise unittest.SkipTest(f"{WORKFLOW_PATH} does not exist")
        cls.text = WORKFLOW_PATH.read_text(encoding="utf-8")

    def test_triggers_on_push_and_pull_request_to_main(self):
        # Cheap and dependency-free: a real YAML parse is not needed to
        # confirm these two keys and branch both appear in the trigger block.
        head = self.text.split("jobs:", 1)[0]
        self.assertRegex(head, r"\bpush:\s*\n\s*branches:\s*\[\s*[\"']main[\"']\s*\]")
        self.assertRegex(head, r"\bpull_request:\s*\n\s*branches:\s*\[\s*[\"']main[\"']\s*\]")

    def test_the_three_verify_commands_run_in_order_and_unguarded(self):
        """Each run line must be its own step (no `|| true`, no `continue-on-error`)
        so the job fails at the first red command, as the pipeline demands."""
        build_m = re.search(r"run:\s*python3 tools/build\.py\s*$", self.text, re.M)
        check_m = re.search(r"run:\s*python3 tools/check_pk3\.py\s*$", self.text, re.M)
        test_m = re.search(r"run:\s*python3 -m unittest discover -s tests\b", self.text, re.M)
        self.assertIsNotNone(build_m, "tools/build.py is not invoked as its own step")
        self.assertIsNotNone(check_m, "tools/check_pk3.py is not invoked as its own step")
        self.assertIsNotNone(test_m, "unittest discover is not invoked as its own step")
        self.assertLess(build_m.start(), check_m.start(), "build must run before check_pk3")
        self.assertLess(check_m.start(), test_m.start(), "check_pk3 must run before the test suite")
        self.assertNotIn("continue-on-error: true", self.text)

    def test_built_pk3_is_uploaded_as_an_artifact(self):
        self.assertIn("actions/upload-artifact", self.text)
        self.assertIn("dist/sovietdoom.pk3", self.text)

    def test_engine_smoke_test_is_named_and_not_executed(self):
        """tools/smoke.py needs GZDoom + an IWAD; this runner has neither.
        The workflow must say so in a clearly named step (mentioning it is
        fine, even expected, in a comment), but must never actually shell
        out to smoke.py or run.sh — only `echo` lines about them."""
        executed = re.findall(r"^\s*(?!#)\S.*\b(?:tools/smoke\.py|tools/run\.sh)\b", self.text, re.M)
        not_echo = [line for line in executed if not re.search(r"\becho\b", line)]
        self.assertEqual([], not_echo, f"smoke.py/run.sh referenced outside an echo/comment: {not_echo}")
        step_names = re.findall(r"- name:\s*(.+)", self.text)
        self.assertTrue(
            any("smoke" in n.lower() and "not run" in n.lower() for n in step_names),
            f"no step name both mentions the smoke test and says it is not run; got {step_names}",
        )
        self.assertIn("GZDoom", self.text)

    def test_hygiene_step_checks_wad_pk3_and_a_five_mb_limit(self):
        self.assertIn("*.wad", self.text)
        self.assertIn("*.pk3", self.text)
        # Decimal or expression form, both acceptable; just don't let the
        # limit silently drift from the 5 MB the pipeline brief specifies.
        self.assertTrue(
            str(FIVE_MB) in self.text or "5 * 1024 * 1024" in self.text,
            "the 5 MB threshold is not literally present in the workflow",
        )

    def test_does_not_try_to_install_or_download_the_engine(self):
        """Decision recorded in docs/PIPELINE.md / README: installing GZDoom
        or downloading Freedoom in CI is not worth a ~23 MB fetch per run,
        yet. This guards against someone adding it back silently."""
        lowered = self.text.lower()
        self.assertNotIn("freedoom2.wad", lowered)
        self.assertNotIn("gzdoom.app", lowered)
        self.assertNotIn("apt-get install", lowered)


if __name__ == "__main__":
    unittest.main()
