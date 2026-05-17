---
name: obsidian-compile
description: "캡처된 자료를 기존 Vault 지식과 비교해 Concept/Claim/Question/Insight/Map/Project/Decision로 재구성한다. 'compile', '캡처된 자료 정리', '인사이트 뽑아줘', '컴파일해줘', '지식으로 바꿔줘', '옵시디언 정리' 같은 요청에 트리거. 새 객체 생성보다 기존 노트 업데이트를 우선하고, 의미 있는 새 연결/모순/패턴/실행 함의가 있을 때만 Insight를 만든다."
---

# Obsidian Compile

Use this skill when captured material should be compared with existing vault knowledge and turned into linked memory.

## Core Rule

Prefer updating existing notes before creating new notes. Create an Insight only when there is a meaningful new connection, contradiction, pattern, or execution implication.

## Workflow

1. Locate captured or source notes to process.
2. Read relevant maps and existing object notes before writing.
3. Identify candidate note types:
   - Concept
   - Claim
   - Question
   - Insight
   - Map
   - Project
   - Decision
4. Search for merge or update candidates.
5. Update existing notes when suitable.
6. Create new object notes only when needed.
7. Update related maps and the Home dashboard.
8. Add log entries in `00_System/logs`.

## Insight Promotion

Promote to Insight when:

- Two or more existing notes become newly connected.
- New evidence changes or challenges a prior belief.
- A repeated pattern becomes visible.
- A question becomes an actionable hypothesis.
- A source changes the direction of a project or decision.

## Safety

- Do not silently overwrite existing conclusions.
- Preserve uncertainty.
- Link evidence to Source notes.
- Mark weak claims as `hypothesis` or `question`, not confident `claim`.

## References

- `../../shared/obsidian-second-brain/references/workflows.md`
- `../../shared/obsidian-second-brain/references/reliability.md`
- `references/compile-workflow.md`
