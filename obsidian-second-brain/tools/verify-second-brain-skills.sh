#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
pack_root="$(cd "$script_dir/.." && pwd)"
cd "$pack_root"

required_files=(
  "README.md"
  "shared/obsidian-second-brain/README.md"
  "shared/obsidian-second-brain/references/vault-structure.md"
  "shared/obsidian-second-brain/references/note-types.md"
  "shared/obsidian-second-brain/references/workflows.md"
  "shared/obsidian-second-brain/references/reliability.md"
  "shared/obsidian-second-brain/templates/source.md"
  "shared/obsidian-second-brain/templates/book-ocr-source.md"
  "shared/obsidian-second-brain/templates/insight.md"
  "shared/obsidian-second-brain/templates/home-dashboard.md"
  "vault-template/00_System/dashboards/Home.md"
  "vault-template/00_System/templates/source.md"
  "vault-template/00_System/templates/book-ocr-source.md"
  "vault-template/00_System/templates/insight.md"
  "tools/init-second-brain-vault.sh"
  "tools/verify-vault.sh"
  "skills/obsidian-init/SKILL.md"
  "skills/obsidian-init/references/init-workflow.md"
  "skills/obsidian-capture/SKILL.md"
  "skills/obsidian-capture/references/book-ocr-workflow.md"
  "skills/obsidian-capture/references/video-transcript-workflow.md"
  "skills/obsidian-compile/SKILL.md"
  "skills/obsidian-retrieve/SKILL.md"
  "skills/obsidian-lint/SKILL.md"
)

for path in "${required_files[@]}"; do
  if [[ ! -f "$path" ]]; then
    echo "Missing required file: $path" >&2
    exit 1
  fi
done

required_dirs=(
  "vault-template/10_Capture/inbox"
  "vault-template/20_Sources/web"
  "vault-template/20_Sources/books"
  "vault-template/20_Sources/books/raw"
  "vault-template/20_Sources/documents"
  "vault-template/20_Sources/papers"
  "vault-template/30_Objects/insights"
  "vault-template/40_Maps/topic-maps"
  "vault-template/50_Execution/projects"
  "vault-template/60_Reviews/lint-reports"
)

for path in "${required_dirs[@]}"; do
  if [[ ! -d "$path" ]]; then
    echo "Missing required directory: $path" >&2
    exit 1
  fi
done

grep -R "name: obsidian-capture" skills/obsidian-capture/SKILL.md >/dev/null
grep -R "name: obsidian-init" skills/obsidian-init/SKILL.md >/dev/null
grep -R "name: obsidian-compile" skills/obsidian-compile/SKILL.md >/dev/null
grep -R "name: obsidian-retrieve" skills/obsidian-retrieve/SKILL.md >/dev/null
grep -R "name: obsidian-lint" skills/obsidian-lint/SKILL.md >/dev/null
grep -R "Init Flow" shared/obsidian-second-brain/references/workflows.md >/dev/null
grep -R "Obsidian second brain vault verification passed" tools/verify-vault.sh >/dev/null
grep -R "Merge Before Create" shared/obsidian-second-brain/references/reliability.md >/dev/null
grep -R "New Connection" shared/obsidian-second-brain/templates/insight.md >/dev/null
grep -R "Review Items" vault-template/00_System/dashboards/Home.md >/dev/null
grep -R "Retrospectives" shared/obsidian-second-brain/templates/project.md >/dev/null
grep -R "Retrospectives" vault-template/00_System/templates/project.md >/dev/null
grep -R "Output" skills/obsidian-retrieve/SKILL.md >/dev/null
grep -R "Broken Links" skills/obsidian-lint/references/lint-workflow.md >/dev/null
grep -R "needs_transcript" skills/obsidian-capture/SKILL.md >/dev/null
grep -R "Video Transcript Workflow" skills/obsidian-capture/references/video-transcript-workflow.md >/dev/null
grep -R "needs_ocr_review" skills/obsidian-capture/SKILL.md >/dev/null
grep -R "Book OCR Workflow" skills/obsidian-capture/references/book-ocr-workflow.md >/dev/null
grep -R "20_Sources/books/raw" skills/obsidian-capture/references/book-ocr-workflow.md >/dev/null
grep -R "source_type: book_ocr" shared/obsidian-second-brain/templates/book-ocr-source.md >/dev/null
grep -R "OCR Basis" vault-template/00_System/templates/book-ocr-source.md >/dev/null

if [[ ! -x tools/init-second-brain-vault.sh ]]; then
  echo "Script is not executable: tools/init-second-brain-vault.sh" >&2
  exit 1
fi

if [[ ! -x tools/verify-vault.sh ]]; then
  echo "Script is not executable: tools/verify-vault.sh" >&2
  exit 1
fi

if grep -R -E "T[B]D|TO[D]O|FIX[M]E" README.md shared vault-template skills >/dev/null; then
  echo "Found placeholder text." >&2
  exit 1
fi

echo "Second brain skill pack verification passed."
