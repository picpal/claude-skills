---
name: obsidian-compile
description: "캡처된 자료를 기존 Vault 지식과 비교해 Concept/Claim/Question/Insight/Map/Project/Decision로 재구성한다. 'compile', '캡처된 자료 정리', '인사이트 뽑아줘', '컴파일해줘', '지식으로 바꿔줘', '옵시디언 정리', 'auto compile', 'compile inbox', 'batch compile' 같은 요청에 트리거. 단일 노트 compile과 inbox 전체를 한 번에 처리하는 Batch Mode 둘 다 지원한다. 새 객체 생성보다 기존 노트 업데이트를 우선하고, 의미 있는 새 연결/모순/패턴/실행 함의가 있을 때만 Insight를 만든다. 사용자가 캡처된 자료의 패턴/연결/정리를 언급하면 명시 요청이 없어도 우선 고려 — 캡처만 쌓이고 compile이 안 되면 vault는 결국 inbox 묘지가 된다."
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
6. Create new object notes only when needed. Write them as Obsidian Flavored Markdown — follow the `obsidian-markdown` skill for properties, wikilinks `[[...]]` (always link to existing concept notes by their exact filename), callouts for contradictions/hypotheses, and `#tag/subtag` hierarchy.
7. Update related maps and the Home dashboard. When a Map needs a dynamic view (e.g. "all open Questions in topic X" or "Claims with stale review_date"), use the `obsidian-bases` skill to create a `.base` file instead of hand-maintaining a list.
8. For Insights that capture a *visual* connection (network of 3+ nodes, flow, cluster), consider a `.canvas` via the `json-canvas` skill — wikilinks suffice for textual links.
9. Add log entries in `00_System/logs`.

## Batch Mode

`compile inbox`, `auto compile`, `batch compile`, `캡처된 자료 전부 정리`, 또는 인자 없이 호출되었고 inbox에 처리 대기 노트가 쌓여 있을 때 발동.

### Phase 1 — Collection

수집 대상 경로:
- `10_Capture/inbox/**/*.md`
- `10_Capture/unprocessed/**/*.md`
- `20_Sources/**/*.md`

Frontmatter `status` 분류:
- **PROCESS**: `captured`, `needs_classification`
- **SKIP & 리포트만**: `needs_transcript`, `needs_ocr_review` — 사람 개입이 필요해 자동 compile하면 잘못된 결론을 굳히게 됨
- **이미 처리됨**: `compiled`, `processed`, 또는 status 없음 — 건너뜀

### Phase 2 — Ordering

신뢰도 높은 순서로 처리. 앞 노트의 compile 결과가 뒤 노트의 컨텍스트가 되므로 순서가 품질에 영향을 줌.

1. `source_type: web` / `document` / `paper` (정제된 텍스트)
2. `source_type: cli_session` (구조화된 로그)
3. `source_type: thought` / `note` (사용자 본인 정리)
4. `source_type: video` with transcript
5. `source_type: book` OCR (review 완료된 것만)

### Phase 3 — Dry-run Preview

기본은 **dry-run 우선**. 실행 전 다음을 출력하고 사용자 confirm:

```
Batch Compile Preview
─────────────────────
PROCESS: N개
  1. [path] → 후보 concept: X, Y / 매칭 기존 노트: [[A]], [[B]] / 계획: update [[A]], create Question Z
  ...
SKIP: M개
  - [path] (needs_transcript)
  ...
예상 작업: update N, create M, insight candidate K
진행하시겠습니까?
```

`auto-confirm` 표현(예: "그냥 돌려", "/schedule로 실행 중", "no preview")이 있으면 preview 건너뛰고 바로 실행.

### Phase 4 — Per-note Execution

각 노트에 대해 [기본 Workflow 1–9](#workflow) 적용. 단:
- 한 노트 실패 시 로그만 남기고 batch 중단하지 않음
- 처리한 노트의 frontmatter `status: compiled` + `compiled_at: <date>` 설정
- 직전 5분 이내 수정된 노트는 skip (capture 진행 중일 가능성)

### Phase 5 — Final Report

```
Batch Compile Done — 2026-05-19
───────────────────────────────
Processed: N (updated K notes, created M notes)
Insights promoted: P (candidates: Q)
Skipped: S (needs_transcript: X, needs_ocr_review: Y, recent edits: Z)
Failed: F (see 00_System/logs/batch-compile-{{date}}.md)

Next:
- needs_transcript {{N}}건: transcript 확보 후 재실행
- 결정 대기 Insight 후보: [[insight-A]], [[insight-B]]
```

### Limits & Safety

- **기본 처리 한도**: 한 번에 20 노트. 초과 시 다음 batch에서.
- **Insight 자동 promotion 금지**: Batch Mode에서는 Insight를 *candidate* 상태로만 생성. 사람이 확인 후 promote. 자동화로 만든 Insight는 후속 compile의 컨텍스트가 되므로 잘못된 Insight 1개가 전체 vault를 오염시킴.
- **모순 발견 시**: 기존 결론 덮어쓰지 말고 `> [!warning] Contradiction with [[...]]` 콜아웃으로 표시 + Question 노트 생성.
- **로그**: 모든 batch 실행은 `00_System/logs/batch-compile-{{date}}.md`에 단일 파일로 누적.

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

## Companion Skills (kepano/obsidian-skills)

Compile decides *what knowledge structure to build*. Delegate the file format:

- `obsidian-markdown` — every Concept/Claim/Question/Insight/Project/Decision note must follow Obsidian Flavored Markdown (frontmatter properties, wikilinks, callouts, tag hierarchy).
- `obsidian-bases` — for Maps and the Home dashboard, prefer a `.base` view (filters, formulas, summaries) over a hand-maintained markdown list when the view should stay live.
- `json-canvas` — optional, when an Insight is better expressed as a visual graph of 3+ linked nodes than as wikilinks in prose.
- `obsidian-cli` — when Obsidian is running, use it for the actual note creation/update so the live graph reflects new links immediately.

## Scheduling Auto-compile

Batch Mode를 정기 실행하려면 사용자가 직접 등록한다 — 이 스킬이 자동으로 스케줄을 만들지 않는다.

권장 트리거 방법:

- **수동 호출**: "compile inbox", "auto compile", 또는 인자 없이 `obsidian-compile` 호출.
- **`/schedule`** (권장 — 백그라운드 routine): 매일 1회 또는 N시간마다.
  ```
  /schedule create --name obsidian-batch-compile \
      --cron "0 22 * * *" \
      --prompt "obsidian-compile batch mode, vault: ~/.../Obsidian/2ndMe, auto-confirm"
  ```
- **`/loop`** (포그라운드 인터벌): 작업 중 inbox를 비우고 싶을 때 임시로.
  ```
  /loop 30m obsidian-compile batch mode auto-confirm
  ```

스케줄 실행에서는 preview를 건너뛰도록 prompt에 `auto-confirm`을 포함해야 한다. preview를 보고 싶다면 매 실행마다 사용자 응답 가능한 환경(터미널 활성)에서만 등록할 것.

## References

- `../../shared/obsidian-second-brain/references/workflows.md`
- `../../shared/obsidian-second-brain/references/reliability.md`
- `references/compile-workflow.md`
- `references/batch-workflow.md`
