#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
output="${1:-$repo_root/dist}"
manifest="$repo_root/distribution/actions.json"

if [[ -e "$output" ]]; then
  echo "output already exists: $output" >&2
  exit 2
fi
mkdir -p "$output"

count=0
while IFS=$'\t' read -r name source marketplace; do
  count=$((count + 1))
  destination="$output/$name"
  mkdir -p "$destination"
  cp "$repo_root/LICENSE" "$destination/LICENSE"
  for asset in "$repo_root/$source"/*; do
    [[ -f "$asset" ]] || continue
    case "$(basename "$asset")" in
      action.yml|README.md) ;;
      *) cp "$asset" "$destination/$(basename "$asset")" ;;
    esac
  done
  if [[ -f "$repo_root/$source/action.yml" ]]; then
    sed 's#\$GITHUB_ACTION_PATH/../../shared/#\$GITHUB_ACTION_PATH/shared/#g' \
      "$repo_root/$source/action.yml" > "$destination/action.yml"
    mkdir -p "$destination/shared"
    cp "$repo_root/shared/install-native.sh" "$destination/shared/install-native.sh"
  fi
  if [[ -f "$repo_root/$source/README.md" ]]; then
    cp "$repo_root/$source/README.md" "$destination/README.md"
  else
    {
      printf '# As Decided %s\n\n' "$name"
      printf 'Generated distribution facade. Authoritative development lives in [asdecided/ci](https://github.com/asdecided/ci/tree/main/%s).\n' "$source"
      if [[ "$marketplace" == "true" ]]; then
        printf '\nUse from GitHub Actions as `asdecided/%s@<version>`.\n' "$name"
      fi
    } > "$destination/README.md"
  fi
done < <(
  python3 -c 'import json,sys; data=json.load(open(sys.argv[1])); [print(x["name"], x["source"], str(x["marketplace"]).lower(), sep="\t") for x in data["facades"]]' "$manifest"
)

if [[ "$count" -ne 6 ]]; then
  echo "expected six facade definitions, packaged $count" >&2
  exit 1
fi
printf 'Packaged six facades in %s\n' "$output"
