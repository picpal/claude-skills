---
name: obsidian-lint
description: "Obsidian Vault의 고아 노트, 중복 개념, 오래된 주장, 끊어진 링크, 방치된 질문, 검토 필요한 결정을 점검해 60_Reviews/lint-reports에 보고서를 만든다. 'vault 점검', 'obsidian lint', '옵시디언 정리', '노트 health check', '죽은 링크 찾아줘', 'vault 건강검진' 같은 요청에 트리거. 자동 삭제/병합은 절대 하지 않고 제안만 한다."
---

# Obsidian Lint

Use this skill when the user wants to clean up, review, or synthesize the health of their Obsidian second-brain vault.

## Core Rule

Lint produces review items and synthesis reports. It does not silently rewrite large parts of the vault.

## Workflow

1. Scan vault structure.
2. Find orphan notes.
3. Find duplicate or merge candidates.
4. Find stale claims and old decisions.
5. Find weak evidence and missing source links.
6. Find broken links.
7. Find unresolved questions.
8. Create a lint report in `60_Reviews/lint-reports`.
9. Update Home dashboard review items.

## Report Sections

- Orphan notes
- Merge candidates
- Stale claims
- Decisions needing review
- Missing evidence
- Broken links
- Unresolved questions
- Suggested next actions

## Safety

- Do not delete notes.
- Do not rewrite source content.
- Do not resolve contradictions automatically.
- Suggest changes clearly so the user can approve them.

## References

- `../../shared/obsidian-second-brain/references/workflows.md`
- `../../shared/obsidian-second-brain/references/reliability.md`
- `references/lint-workflow.md`
