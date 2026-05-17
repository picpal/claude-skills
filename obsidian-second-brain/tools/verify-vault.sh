#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: verify-vault.sh /path/to/obsidian-vault" >&2
}

if [[ $# -ne 1 ]]; then
  usage
  exit 2
fi

vault_root="$1"
missing=()

if [[ ! -d "$vault_root" ]]; then
  echo "Vault directory does not exist: $vault_root" >&2
  exit 1
fi

required_dirs=(
  "00_System/dashboards"
  "00_System/templates"
  "00_System/schemas"
  "10_Capture/inbox"
  "10_Capture/unprocessed"
  "20_Sources/sessions"
  "20_Sources/web"
  "20_Sources/videos"
  "20_Sources/images"
  "20_Sources/documents"
  "20_Sources/books"
  "20_Sources/books/raw"
  "20_Sources/papers"
  "30_Objects/concepts"
  "30_Objects/claims"
  "30_Objects/questions"
  "30_Objects/insights"
  "30_Objects/decisions"
  "40_Maps/topic-maps"
  "50_Execution/projects"
  "60_Reviews/lint-reports"
  "_assets/images"
)

required_files=(
  "00_System/dashboards/Home.md"
  "00_System/schemas/note-types.md"
  "00_System/templates/source.md"
  "00_System/templates/book-ocr-source.md"
  "00_System/templates/insight.md"
  "00_System/templates/project.md"
  "00_System/templates/decision.md"
)

for path in "${required_dirs[@]}"; do
  if [[ ! -d "$vault_root/$path" ]]; then
    missing+=("dir: $path")
  fi
done

for path in "${required_files[@]}"; do
  if [[ ! -f "$vault_root/$path" ]]; then
    missing+=("file: $path")
  fi
done

if [[ -f "$vault_root/00_System/dashboards/Home.md" ]] &&
  ! grep -R "Review Items" "$vault_root/00_System/dashboards/Home.md" >/dev/null; then
  missing+=("content: 00_System/dashboards/Home.md lacks Review Items")
fi

if [[ -f "$vault_root/00_System/templates/project.md" ]] &&
  ! grep -R "Retrospectives" "$vault_root/00_System/templates/project.md" >/dev/null; then
  missing+=("content: 00_System/templates/project.md lacks Retrospectives")
fi

if [[ -f "$vault_root/00_System/templates/insight.md" ]] &&
  ! grep -R "New Connection" "$vault_root/00_System/templates/insight.md" >/dev/null; then
  missing+=("content: 00_System/templates/insight.md lacks New Connection")
fi

if [[ ${#missing[@]} -gt 0 ]]; then
  echo "Obsidian second brain vault verification failed." >&2
  printf 'Missing or incompatible %s\n' "${missing[@]}" >&2
  exit 1
fi

echo "Obsidian second brain vault verification passed."
