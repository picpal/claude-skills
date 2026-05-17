---
name: obsidian-lint
description: "Obsidian Vault의 고아 노트, 중복 개념, 오래된 주장, 끊어진 링크, 방치된 질문, 검토 필요한 결정을 점검해 60_Reviews/lint-reports에 보고서를 만든다. 'vault 점검', 'obsidian lint', '옵시디언 정리', '노트 health check', '죽은 링크 찾아줘', 'vault 건강검진' 같은 요청에 트리거. 자동 삭제/병합은 절대 하지 않고 제안만 한다. 정기 점검은 사용자가 잊기 쉬우니 vault 건강·정리·검토 키워드가 보이면 명시 요청이 없어도 적극 발동."
---

# Obsidian Lint

Use this skill when the user wants to clean up, review, or synthesize the health of their Obsidian second-brain vault.

## Core Rule

Lint produces review items and synthesis reports. It does not silently rewrite large parts of the vault.

**Why:** A vault is the user's external memory and contains their unfinished thinking — silent auto-merges or deletions destroy provenance and erode trust irreversibly. Lint surfaces work; the user decides what to act on.

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

## Example

**Input:** "vault 전체 점검해줘" (vault에 `[[llm-context-claim]]`이 `[[broken-link-to-context-cost]]`를 참조하지만 후자가 없음; `[[llm-context-claim]]`의 review_date가 2025-06-01로 오래 지남; orphan note 2개 존재)

**Output:** `60_Reviews/lint-reports/2026-05-17-lint.md`

```markdown
---
type: lint-report
created: 2026-05-17
---
# Vault Lint Report — 2026-05-17

## Orphan Notes
- `30_Objects/concepts/orphan-A.md`
- `30_Objects/questions/orphan-B.md`

## Broken Links
- `30_Objects/claims/llm-context-claim.md` → `[[broken-link-to-context-cost]]` (대상 노트 없음)

## Stale Claims
- `30_Objects/claims/llm-context-claim.md` review_date: 2025-06-01 (~12개월 경과)

## Decisions Needing Review
(없음)

## Missing Evidence
(없음)

## Unresolved Questions
- `30_Objects/questions/q-codex-claude-separation.md` (created: 2026-04-25, 답변 없이 3주+)

## Suggested Next Actions
1. orphan 2개: Map에 연결할지, 삭제 후보인지 결정.
2. broken link: `[[broken-link-to-context-cost]]` 작성 또는 참조 제거.
3. stale claim: 최근 evidence 확인 후 confidence 갱신 또는 hypothesis 강등.
```

자동 삭제·자동 병합 **금지**. 위 4개 항목은 모두 *제안*이며, 사용자가 승인 후 별도로 적용. Home 대시보드 "Review Items"에 이 보고서 링크 추가.

## References

- `../../shared/obsidian-second-brain/references/workflows.md`
- `../../shared/obsidian-second-brain/references/reliability.md`
- `references/lint-workflow.md`
