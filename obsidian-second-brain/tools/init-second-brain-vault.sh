#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
pack_root="$(cd "$script_dir/.." && pwd)"
template_root="$pack_root/vault-template"

usage() {
  echo "Usage: init-second-brain-vault.sh /path/to/obsidian-vault" >&2
}

if [[ $# -ne 1 ]]; then
  usage
  exit 2
fi

vault_root="$1"

if [[ ! -d "$template_root" ]]; then
  echo "Missing vault template: $template_root" >&2
  exit 1
fi

mkdir -p "$vault_root"

created_dirs=0
copied_files=0
kept_files=0

while IFS= read -r -d '' source_dir; do
  rel="${source_dir#$template_root}"
  rel="${rel#/}"

  if [[ -z "$rel" ]]; then
    continue
  fi

  target_dir="$vault_root/$rel"
  if [[ ! -d "$target_dir" ]]; then
    mkdir -p "$target_dir"
    created_dirs=$((created_dirs + 1))
  fi
done < <(find "$template_root" -type d -print0)

while IFS= read -r -d '' source_file; do
  rel="${source_file#$template_root/}"
  target_file="$vault_root/$rel"

  mkdir -p "$(dirname "$target_file")"

  if [[ -e "$target_file" ]]; then
    kept_files=$((kept_files + 1))
    continue
  fi

  cp "$source_file" "$target_file"
  copied_files=$((copied_files + 1))
done < <(find "$template_root" -type f -print0)

cat <<REPORT
Initialized Obsidian second brain vault.
Vault: $vault_root
Directories created: $created_dirs
Files copied: $copied_files
Existing files kept: $kept_files
Run verification: $pack_root/tools/verify-vault.sh "$vault_root"
REPORT
