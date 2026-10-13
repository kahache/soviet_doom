#!/usr/bin/env bash
# Run the pytest/unittest suite under `coverage` and report which branches
# of our own tooling (tools/) actually execute. Dev-only: `coverage` lives
# in .venv/ (see CLAUDE.md "Setup and commands"), never in the stdlib-only
# build path that tools/build.py uses to produce dist/sovietdoom.pk3.
#
# Usage:
#   tools/coverage.sh            # run suite, print report, write HTML
#   tools/coverage.sh --no-html  # skip the HTML report (faster)
#
# Output:
#   stdout: per-file report, worst coverage first, total last
#   logs/coverage/html/index.html: browsable HTML report (gitignored)
#   logs/coverage/.coverage: raw coverage data (gitignored)
#
# Exit code is the suite's (0 if all tests passed), NOT the coverage
# percentage - coverage is measured and reported even on a red suite; a
# failing test still executes code and that execution still counts.

set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PY="$ROOT/.venv/bin/python"
[[ -x "$VENV_PY" ]] || VENV_PY="$ROOT/.venv/Scripts/python.exe"   # Windows venv layout
COV_DIR="$ROOT/logs/coverage"
DATA_FILE="$COV_DIR/.coverage"
HTML_DIR="$COV_DIR/html"
WRITE_HTML=1

for arg in "$@"; do
  case "$arg" in
    --no-html) WRITE_HTML=0 ;;
    *)
      echo "coverage.sh: unknown argument '$arg'" >&2
      exit 2
      ;;
  esac
done

if [[ ! -x "$VENV_PY" ]]; then
  echo "coverage.sh: $VENV_PY not found; run:" >&2
  echo "  python3 -m venv .venv && .venv/bin/python -m pip install coverage" >&2
  exit 3
fi

if ! "$VENV_PY" -c "import coverage" >/dev/null 2>&1; then
  echo "coverage.sh: 'coverage' not installed in .venv/; run:" >&2
  echo "  .venv/bin/python -m pip install coverage" >&2
  exit 3
fi

mkdir -p "$COV_DIR"
rm -f "$DATA_FILE"

# --rcfile picks up the versioned .coveragerc at the repo root (source,
# branch mode, and the argparse/__main__ exclusions). COVERAGE_FILE keeps
# the raw data out of the repo root, under the gitignored logs/ tree.
COVERAGE_FILE="$DATA_FILE" "$VENV_PY" -m coverage run --rcfile="$ROOT/.coveragerc" \
  -m unittest discover -s "$ROOT/tests" -v
SUITE_RC=$?

echo
echo "== coverage: tools/ (branches executed by the suite above) =="
# --sort=cover: worst file first, so the gaps that matter are on top, not
# buried after dozens of fully-covered files. The grand Total line always
# prints last regardless of sort order.
COVERAGE_FILE="$DATA_FILE" "$VENV_PY" -m coverage report --rcfile="$ROOT/.coveragerc" \
  --sort=cover

if [[ "$WRITE_HTML" -eq 1 ]]; then
  COVERAGE_FILE="$DATA_FILE" "$VENV_PY" -m coverage html --rcfile="$ROOT/.coveragerc" \
    -d "$HTML_DIR"
  echo
  echo "HTML report: $HTML_DIR/index.html"
fi

if [[ "$SUITE_RC" -ne 0 ]]; then
  echo
  echo "NOTE: the test suite above did NOT pass (exit $SUITE_RC)." >&2
  echo "Coverage was still measured and reported: code a failing test" >&2
  echo "exercises on its way to failing still counts as executed." >&2
fi

exit "$SUITE_RC"
