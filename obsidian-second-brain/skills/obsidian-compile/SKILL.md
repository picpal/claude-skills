---
name: obsidian-compile
description: "캡처된 자료를 기존 Vault 지식과 비교해 Concept/Claim/Question/Insight/Map/Project/Decision로 재구성한다. 'compile', '캡처된 자료 정리', '인사이트 뽑아줘', '컴파일해줘', '지식으로 바꿔줘', '옵시디언 정리' 같은 요청에 트리거. 새 객체 생성보다 기존 노트 업데이트를 우선하고, 의미 있는 새 연결/모순/패턴/실행 함의가 있을 때만 Insight를 만든다. 사용자가 캡처된 자료의 패턴/연결/정리를 언급하면 명시 요청이 없어도 우선 고려 — 캡처만 쌓이고 compile이 안 되면 vault는 결국 inbox 묘지가 된다."
---

# Obsidian Compile

Use this skill when captured material should be compared with existing vault knowledge and turned into linked memory.

## Core Rule

Prefer updating existing notes before creating new notes. Create an Insight only when there is a meaningful new connection, contradiction, pattern, or execution implication.

**Why:** Vault value comes from *connections per note*, not *note count*. A duplicate concept fragments search results and forces the next compile pass to reconcile two versions of the same idea — that cost compounds. New material gains leverage when bonded to existing structure.

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

## Example

**Input:** vault에 `10_Capture/inbox/2026-05-12-agent-design.md` ("AI 에이전트는 reasoning보다 trustable orchestration이 핵심")가 들어와 있음. 기존에 `30_Objects/concepts/ai-agent.md`와 `40_Maps/topic-maps/ai-llm-map.md`가 이미 존재.

**Output (선호 동작):**
- **새 concept 생성하지 않음.** `30_Objects/concepts/ai-agent.md`의 `## Key Points`에 "trustable orchestration" 한 줄 추가, `## Sources`에 `[[2026-05-12-agent-design]]` 링크 추가.
- `40_Maps/topic-maps/ai-llm-map.md`의 `## 현재 요약` 또는 `## Tensions`에 새 트레이드오프 한 줄 반영.
- `00_System/logs/`에 변경 항목 1줄 로그.
- Insight 노트는 **만들지 않음** — 단일 메모로는 의미 있는 *새 연결/모순/패턴/실행 함의* 기준을 충족하지 못함.

**언제 Insight를 만드는가:** 두 개 이상의 노트가 새로 연결되거나, 기존 결정이 흔들리는 evidence가 들어왔거나, 반복 패턴이 처음 보일 때.

## References

- `../../shared/obsidian-second-brain/references/workflows.md`
- `../../shared/obsidian-second-brain/references/reliability.md`
- `references/compile-workflow.md`
