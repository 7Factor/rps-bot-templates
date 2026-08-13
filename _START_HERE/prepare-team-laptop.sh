#!/usr/bin/env bash
set -eo pipefail

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
LABEL='Laptop preparation failure'
languages=()

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
  printf 'Usage: %s [--language LANGUAGE_ID]...\n' "$0"
}

while [[ $# -gt 0 ]]; do
  case $1 in
    --language)
      shift
      [[ $# -gt 0 ]] || { usage >&2; exit 2; }
      languages+=("$1")
      ;;
    -h|--help) usage; exit 0 ;;
    *) usage >&2; exit 2 ;;
  esac
  shift
done
if [[ ${#languages[@]} -eq 0 ]]; then
  while IFS= read -r language; do languages+=("$language"); done < <(available_languages)
fi
for language in "${languages[@]}"; do require_language "$language"; done

platform=$(docker version --format '{{.Server.Os}}/{{.Server.Arch}}' 2>&1) || fail "$platform"
case $platform in linux/amd64|linux/arm64) ;; *) fail "unsupported Docker server platform '$platform'; use native linux/amd64 or linux/arm64" ;; esac

runner_commit=$(sed -n '/"runner"[[:space:]]*:/,$ s/.*"commit"[[:space:]]*:[[:space:]]*"\([0-9a-f]*\)".*/\1/p' "$ROOT/core-tool.lock.json" | head -n 1)
catalog_relative=$(sed -n 's/.*"path"[[:space:]]*:[[:space:]]*"\(language_environments\/[^"]*\/catalog\.json\)".*/\1/p' "$ROOT/core-tool.lock.json" | head -n 1)
[[ -n $runner_commit && -n $catalog_relative ]] || fail 'core-tool.lock.json does not identify the pinned catalog'

core=${RPS_CORE_PATH:-"$ROOT/.core/rps-tournament"}
if [[ -d $core ]]; then
  actual_commit=$(git -C "$core" rev-parse HEAD 2>/dev/null || true)
  [[ $actual_commit == "$runner_commit" && -z $(git -C "$core" status --porcelain 2>/dev/null) ]] || \
    fail "existing pinned core checkout is not clean at $runner_commit: $core"
else
  mkdir -p "$(dirname -- "$core")"
  git clone --quiet --no-checkout "$ROOT/core-tool.bundle" "$core" || fail 'could not clone the bundled core history'
  git -c advice.detachedHead=false -C "$core" checkout --quiet --detach "$runner_commit" || fail "bundled core commit $runner_commit is unavailable"
fi
catalog="$core/$catalog_relative"
[[ -f $catalog ]] || fail "pinned catalog is missing: $catalog"

images=()
for language in "${languages[@]}"; do
  descriptor=$(descriptor_for_language "$language") || fail "descriptor for '$language' is unavailable"
  environment=$(json_string_field "$descriptor" language_environment)
  runtimes="$catalog"
  runtimes="${runtimes%/catalog.json}/$environment/runtimes.json"
  [[ -f $runtimes ]] || fail "runtime definition for '$environment' is missing"
  compact=$(tr -d '\n' < "$runtimes")
  segment=$(printf '%s\n' "$compact" | sed 's|.*"'"$platform"'"[[:space:]]*:[[:space:]]*{||; s|"linux/[a-z0-9]*"[[:space:]]*:.*||')
  found=$(printf '%s\n' "$segment" | sed 's/"image"[[:space:]]*:[[:space:]]*"/\
/g' | sed -n 's/^\([^"]*@sha256:[0-9a-f]*\)".*/\1/p')
  [[ -n $found ]] || fail "the pinned Language Environment '$environment' has no runtime for $platform"
  while IFS= read -r image; do
    duplicate=false
    for existing in "${images[@]}"; do [[ $existing == "$image" ]] && duplicate=true; done
    $duplicate || images+=("$image")
  done <<< "$found"
done

printf 'Detected platform: %s\n' "$platform"
language_list=
for language in "${languages[@]}"; do
  [[ -n $language_list ]] && language_list="$language_list, $language" || language_list=$language
done
printf 'Languages: %s\n' "$language_list"
printf '%s pinned image(s) to pull.\n' "${#images[@]}"
failures=()
for image in "${images[@]}"; do
  printf 'Pulling %s ...\n' "$image"
  docker pull "$image" || failures+=("$image")
done
if [[ ${#failures[@]} -gt 0 ]]; then
  printf 'Failed to pull:\n' >&2
  printf '  %s\n' "${failures[@]}" >&2
  exit 1
fi
printf 'All pinned images are cached. check-team-template and validate-team can now run offline.\n'
