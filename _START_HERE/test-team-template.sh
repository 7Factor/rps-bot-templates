#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
SUBMISSION="$ROOT/team-submission.json"

fail() {
  printf 'Local test failure: %s\n' "$1" >&2
  exit 2
}

[[ -f $SUBMISSION && ! -L $SUBMISSION ]] || \
  fail 'team-submission.json is missing; run start-team-template.sh first'

format_version=$(sed -n 's/.*"format_version"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$SUBMISSION" | head -n 1)
language=$(sed -n 's/.*"language_id"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$SUBMISSION" | head -n 1)
[[ $format_version == rps-team-submission-v1 && $language =~ ^[a-z][a-z0-9-]*$ ]] || \
  fail 'team-submission.json is invalid; ask an organizer for help'

command -v python3 >/dev/null 2>&1 || \
  fail 'Python 3 is required by the repository validation commands'
command -v docker >/dev/null 2>&1 || fail 'Docker is not installed or is not on PATH'
docker version >/dev/null 2>&1 || fail 'Docker is installed, but its engine is not running'

printf 'Validating your %s Team Source and pulling missing pinned images...\n' "$language"
"$ROOT/validate-team" --allow-pull

printf '\nRunning the Team Template Docker check...\n'
"$ROOT/check-team-template" --template "$language" --mode docker

printf '\nLocal tests passed. Commit your changes and push your Team branch.\n'
