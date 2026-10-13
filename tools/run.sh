#!/usr/bin/env bash
# Build the PK3 and launch GZDoom on it, always logging to logs/gzdoom.log.
#
# Usage:
#   tools/run.sh                     # MAP01, default skill
#   MAP=MAP01 SKILL=4 tools/run.sh   # choose map / skill (1..5)
#   IWAD=/path/doom2.wad tools/run.sh
#   GZDOOM=/path/to/gzdoom tools/run.sh
#   tools/run.sh +vid_fps 1 -nosound # extra args go straight to gzdoom
#   SD_NO_BUILD=1 tools/run.sh       # skip the build step
#
# Exit codes: 2 gzdoom not found, 3 IWAD not found, 4 build failed.

set -euo pipefail

# --- engine gate -------------------------------------------------------
# Running GZDoom opens a window on the CEO's desktop and steals focus. On
# 2026-10-13 agents were opening three or four windows every twenty seconds
# and he could not work. macOS GZDoom is a Cocoa app with no documented
# headless mode, so the only reliable fix is not to run it.
# AGENTS: do not set this. Verify with `tools/verify.py fast` and say in your
# summary that the engine run is owed; the PM batches them.
if [ "${SD_ALLOW_ENGINE:-}" != "1" ]; then
  echo "run.sh: refusing to start GZDoom (set SD_ALLOW_ENGINE=1 to override)." >&2
  echo "  Agents: use 'tools/verify.py fast' and report that the engine run is owed." >&2
  exit 9
fi


ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MOD_NAME="sovietdoom"
PK3="$ROOT/dist/$MOD_NAME.pk3"
LOG="$ROOT/logs/gzdoom.log"
MAP="${MAP:-MAP01}"

die() { echo "run.sh: $1" >&2; exit "$2"; }

# --- GZDoom binary --------------------------------------------------------
find_gzdoom() {
	if [ -n "${GZDOOM:-}" ]; then
		[ -x "$GZDOOM" ] && { echo "$GZDOOM"; return; }
		die "GZDOOM=$GZDOOM is not executable" 2
	fi
	local candidates=(
		"/Applications/GZDoom.app/Contents/MacOS/gzdoom"
		"$HOME/Applications/GZDoom.app/Contents/MacOS/gzdoom"
	)
	local c
	for c in "${candidates[@]}"; do
		[ -x "$c" ] && { echo "$c"; return; }
	done
	if command -v gzdoom >/dev/null 2>&1; then
		command -v gzdoom; return
	fi
	die "gzdoom not found. Install GZDoom (brew install --cask gzdoom) or set GZDOOM=/path/to/gzdoom" 2
}

# --- IWAD -----------------------------------------------------------------
find_iwad() {
	if [ -n "${IWAD:-}" ]; then
		[ -f "$IWAD" ] && { echo "$IWAD"; return; }
		die "IWAD=$IWAD does not exist" 3
	fi
	local dirs=(
		"$ROOT/iwads"
		"$HOME/Library/Application Support/gzdoom"
		"${DOOMWADDIR:-}"
	)
	local names=("freedoom2.wad" "doom2.wad" "DOOM2.WAD")
	local d n
	for d in "${dirs[@]}"; do
		[ -n "$d" ] && [ -d "$d" ] || continue
		for n in "${names[@]}"; do
			[ -f "$d/$n" ] && { echo "$d/$n"; return; }
		done
	done
	die "no IWAD found (looked for freedoom2.wad / doom2.wad in $ROOT/iwads and ~/Library/Application Support/gzdoom). Set IWAD=/path/to/file.wad" 3
}

GZDOOM_BIN="$(find_gzdoom)"
IWAD_PATH="$(find_iwad)"

# --- Build ----------------------------------------------------------------
if [ -z "${SD_NO_BUILD:-}" ]; then
	python3 "$ROOT/tools/build.py" --quiet || die "build failed" 4
fi
[ -f "$PK3" ] || die "$PK3 missing; run python3 tools/build.py" 4

mkdir -p "$ROOT/logs"
rm -f "$LOG"

ARGS=(-iwad "$IWAD_PATH" -file "$PK3" +logfile "$LOG")
if [ -n "${SKILL:-}" ]; then
	ARGS+=(-skill "$SKILL")
fi
ARGS+=(+map "$MAP")

echo "gzdoom : $GZDOOM_BIN"
echo "iwad   : $IWAD_PATH"
echo "pk3    : $PK3"
echo "log    : $LOG"
echo "args   : ${ARGS[*]} $*"
exec "$GZDOOM_BIN" "${ARGS[@]}" "$@"
