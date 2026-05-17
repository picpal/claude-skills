---
name: obsidian-retrieve
description: "Obsidian Vault 안의 Maps → Objects → Sources 순으로 따라가며 근거 링크와 추론을 분리해 질문에 답한다. 'vault에 질문', '내 노트 기준으로', 'retrieve', '내가 정리한 자료로 답해줘', '옵시디언에서 찾아줘', '내 vault에서 검색' 같은 요청에 트리거. 근거가 약하면 confidence: low 또는 needs_evidence로 표시한다. 사용자가 vault·노트·second brain 안의 정보로 답을 원하는 듯한 질문이면 명시 요청이 없어도 우선 고려 — 일반 지식 답변과 vault 근거 답변은 가치가 다르다."
---

# Obsidian Retrieve

Use this skill when the user asks a question that should be answered from the Obsidian second-brain vault.

## Core Rule

Start from Maps, then follow Object links, then open Source notes for evidence. Distinguish evidence from inference.

**Why:** Maps carry the latest synthesis of a topic — they compress what the user already knows. Starting there narrows the search space fast; jumping straight to Sources loses that compression and produces scattered, low-confidence answers. Mixing evidence and inference in the same paragraph erodes the trust that made the vault worth building.

## Workflow

1. Identify the question and relevant topic area.
2. Read relevant `40_Maps` notes first.
3. Follow links into `30_Objects`.
4. Open supporting `20_Sources`.
5. Answer with evidence links and confidence.
6. If retrieval creates new value, save a candidate:
   - Insight
   - Question
   - Decision
   - Project action
   - Output note

## Answer Format

Use:

```markdown
## Answer

{{answer}}

## Evidence

- [[source-note]]: {{why_it_matters}}

## Inference

{{what_is_reasoned_beyond_sources}}

## Confidence

low | medium | high

## New Memory Candidates

- Insight:
- Question:
- Decision:
- Project action:
- Output:
```

## Safety

- Do not hide weak evidence.
- Do not answer from memory alone when vault notes are available.
- Mark missing evidence as `needs_evidence`.

## Example

**Input:** "내 vault 기준으로 'AI 에이전트의 핵심 트레이드오프'에 답해줘" (vault에는 `40_Maps/topic-maps/ai-llm-map.md`, `30_Objects/concepts/ai-agent.md`, `30_Objects/concepts/skill-architecture.md`, `20_Sources/web/2026-05-10-skill-system.md` 존재)

**Output:**

```markdown
## Answer
AI 에이전트의 핵심 트레이드오프는 *reasoning capability* vs *trustable orchestration*이며, 컨텍스트 비용과 도메인 지식 주입 방식이 그 분기점을 결정한다.

## Evidence
- [[ai-llm-map]]: "AI 에이전트의 핵심 가치는 reasoning보다 trustable orchestration"이라는 latest synthesis 라인
- [[ai-agent]]: 정의 — "환경을 관찰하고 도구를 사용해 자율적으로 행동" + 챗봇과의 대비
- [[skill-architecture]]: "시스템 프롬프트는 모든 호출에 들어가지만, skill은 trigger될 때만 load됨" → 컨텍스트 비용 trade-off의 구체화
- [[2026-05-10-skill-system]]: skill triggering이 description으로 결정됨 → 도메인 지식 주입 방식의 한 사례

## Inference
세 노트가 같은 분기축(reasoning depth vs orchestration trust + context budget)을 다른 각도에서 비추고 있다. Vault 안에 명시적인 통합 문장은 없으나 Map의 합성 라인과 concept 정의를 합치면 위 답이 나온다.

## Confidence
medium — Map은 latest_synthesis: 2026-05-01로 비교적 최근. 더 강한 답을 위해서는 trade-off별 구체 사례 source가 필요 (currently needs_evidence).

## New Memory Candidates
- Insight: "에이전트 설계의 분기축은 reasoning vs orchestration, context vs domain injection의 2×2일 수 있다"
- Question: "trustable orchestration을 정량 측정할 metric은?"
```

답이 vault 근거를 못 찾으면 `confidence: low` + `needs_evidence`로 명시하며, 일반 지식만으로 채워 넣지 않는다.

## References

- `../../shared/obsidian-second-brain/references/workflows.md`
- `../../shared/obsidian-second-brain/references/reliability.md`
- `references/retrieve-workflow.md`
