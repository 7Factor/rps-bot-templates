#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
LABEL='Team start failure'
language=
team=
list=false

fail() {
  printf '%s: %s\n' "$LABEL" "$1" >&2
  exit 2
}

json_string_field() {
  sed -n 's/.*"'"$2"'"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$1" | head -n 1
}

available_languages() {
  sed -n 's/.*"language_id"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$ROOT/team-templates.json"
}

languages_csv() {
  local result= item
  while IFS= read -r item; do
    [[ -n $result ]] && result="$result, $item" || result=$item
  done < <(available_languages)
  printf '%s\n' "$result"
}

require_language() {
  local item
  while IFS= read -r item; do [[ $item == "$1" ]] && return 0; done < <(available_languages)
  fail "unknown language '$1'; available: $(languages_csv)"
}

descriptor_for_language() {
  local current= line
  while IFS= read -r line; do
    case $line in
      *'"language_id"'*) current=$(printf '%s\n' "$line" | sed -n 's/.*"language_id"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p') ;;
      *'"descriptor"'*)
        if [[ $current == "$1" ]]; then
          printf '%s/%s\n' "$ROOT" "$(printf '%s\n' "$line" | sed -n 's/.*"descriptor"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')"
          return 0
        fi
        ;;
    esac
  done < "$ROOT/team-templates.json"
  return 1
}

usage() {
  printf 'Usage: %s --language LANGUAGE_ID --team TEAM_SLUG\n       %s --list\n' "$0" "$0"
}

while [[ $# -gt 0 ]]; do
  case $1 in
    --language) shift; [[ $# -gt 0 ]] || { usage >&2; exit 2; }; language=$1 ;;
    --team) shift; [[ $# -gt 0 ]] || { usage >&2; exit 2; }; team=$1 ;;
    --list) list=true ;;
    -h|--help) usage; exit 0 ;;
    *) usage >&2; exit 2 ;;
  esac
  shift
done

if $list; then
  printf 'Available languages: %s\n' "$(languages_csv)"
  exit 0
fi
[[ -n $language ]] || { printf 'Available languages: %s\n' "$(languages_csv)"; usage >&2; exit 2; }
require_language "$language"
[[ $team =~ ^[a-z][a-z0-9-]*$ ]] || \
  fail '--team is required and must be lowercase letters, digits, and hyphens (e.g. red-rockets)'

git -C "$ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1 || fail "not a git checkout of $ROOT"
[[ -z $(git -C "$ROOT" status --porcelain) ]] || \
  fail 'the working tree has uncommitted changes; commit or stash them first'
branch="team/$team"
if git -C "$ROOT" rev-parse -q --verify "refs/heads/$branch" >/dev/null; then
  fail "branch '$branch' already exists; check it out directly with \`git checkout $branch\`"
fi

descriptor=$(descriptor_for_language "$language") || fail "descriptor for '$language' is unavailable"
release_tag=$(json_string_field "$descriptor" release_tag)
team_source=$(json_string_field "$descriptor" team_source_path)
guide=$(json_string_field "$descriptor" participant_guidance_path)
if git -C "$ROOT" rev-parse -q --verify "refs/tags/$release_tag" >/dev/null; then
  start_point="$release_tag^{}"
  start_label="published Template Release $release_tag"
else
  default_remote=$(git -C "$ROOT" symbolic-ref -q --short refs/remotes/origin/HEAD 2>/dev/null || true)
  start_point=${default_remote#origin/}
  [[ -n $start_point ]] || start_point=main
  start_label="tip of $start_point (no $release_tag Template Release has been published yet)"
fi

git -C "$ROOT" checkout -b "$branch" "$start_point"
submission="$ROOT/team-submission.json"
[[ ! -e $submission && ! -L $submission ]] || fail "$submission already exists; it was not replaced"
( set -o noclobber
  printf '{\n  "format_version": "rps-team-submission-v1",\n  "language_id": "%s"\n}\n' "$language" > "$submission"
) || fail "could not create $submission"

printf 'Created branch %s from %s.\n' "$branch" "$start_label"
printf 'Recorded the Team Template selection in team-submission.json.\n'
printf 'Edit your Team Source here:\n'
find "$ROOT/$team_source" -maxdepth 1 -type f -print | LC_ALL=C sort | while IFS= read -r path; do
  printf '  %s\n' "${path#"$ROOT/"}"
done
printf 'Guide: %s\n\n' "$guide"
printf 'Next steps:\n'
printf '  git add team-submission.json\n'
printf '  git commit -m "Select %s Team Template"\n' "$language"
printf '  ./check-team-template --template %s --mode docker\n' "$language"
printf '  ./validate-team --template %s\n' "$language"
