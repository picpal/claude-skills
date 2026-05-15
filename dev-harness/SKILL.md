---
name: dev-harness
description: "코드 작업 요청(기능 추가, 버그 수정, 리팩토링, 마이그레이션)을 Classify → Brainstorm → Plan → Execute → QA → Lesson 6단계 파이프라인으로 실행하는 하네스. 진입 시 .harness/lessons.md를 자동 로드해 과거 학습을 능동 제약으로 주입한다. config.yaml로 각 phase의 외부 스킬을 교체 가능 (기본: superpowers + gstack:qa). semi-auto — 분기점 4개에서만 사용자 승인. '하네스 돌려줘', 'dev harness로', '파이프라인으로 진행', '하네스 실행' 같은 요청에 트리거. 단순 질문/읽기 작업에는 사용하지 않는다."
---

# dev-harness

## 언제 사용

- 코드 변경을 동반하는 모든 요청 (기능 추가, 버그 수정, 리팩토링, 마이그레이션)
- 진행 상태를 추적하고 lesson으로 컴파운드하고 싶을 때
- "하네스 돌려줘", "파이프라인으로 진행", "단계별로" 같은 요청

## 사용하지 말 것

- 단순 질문/조회 ("X가 뭐야?", "Y 파일 보여줘")
- 1줄 즉시 수정 ("오타 고쳐줘") — 직접 처리
- 외부 시스템 조작 (Slack, Discord, 이메일 등)

---

## Phase 0 — Bootstrap (lesson 재투입의 핵심 단계)

### 단계

1. **Project root 결정**:
   ```bash
   git rev-parse --show-toplevel
   ```
   실패 시 cwd 사용 + warning: "git repo가 아님. safe tag 단계 스킵 예정"

2. **.harness/ 디렉토리 확보**:
   ```bash
   test -d <root>/.harness || mkdir -p <root>/.harness
   ```

3. **lessons.md 재투입** ⚠️ **이 단계가 가장 중요**:
   - `test -f <root>/.harness/lessons.md` 체크
   - **존재 시**:
     - Read 도구로 전체 내용 로드
     - `---` 구분자 기준 마지막 5 entry 추출
     - 채팅에 **verbatim 인용** (필터링/요약 절대 금지)
     - 인용 직후 다음 한 줄 선언:
       > **"이번 세션 동안 위 lesson을 능동 제약(active constraint)으로 취급한다. 위반 가능성이 보이면 진행 전 사용자에게 확인한다."**
   - **부재 시**: "lesson 이력 없음, 새 파이프라인 시작" 한 줄 안내

4. **state.json Read or Create**:
   - 존재 시 → Read → `current_phase` 확인
     - `idle` 또는 `done` → 신규 진행
     - 그 외 → **Phase 7 Resume**으로 분기
   - 부재 시 → 다음 초기 JSON 작성:
     ```json
     {
       "version": 1,
       "current_phase": "bootstrap",
       "tier": null,
       "complexity_score": null,
       "score_breakdown": {},
       "started_at": "<ISO-8601 now>",
       "finished_at": null,
       "completed_phases": [],
       "blocked_reason": null,
       "last_safe_tag": null,
       "config_snapshot": {},
       "user_request_summary": null
     }
     ```

5. **config.yaml 로드**:
   - `<skill-root>/config.yaml` Read
   - 각 phase의 `type`/`id`/`value`/`path`/`fallback` 파싱
   - state.json `config_snapshot`에 기록

6. **사용자 요청 요약 + 진행 확인** — **[승인 1]**:
   ```
   요청 요약: <40자 이내 요약>
   Phase 1 (Classify)부터 진행할까요?
   ```

`state.json.user_request_summary` 기록 후 사용자 응답 대기.

---

## Phase 1 — Classify (복잡도 점수 + Tier 결정)

### 단계

1. `references/classify-rubric.md` Read

2. baton 6기준 점수 계산:

| 기준 | 점수 |
|------|------|
| 변경 파일 수 (1점/파일, max 5) | 0–5 |
| 크로스서비스 의존 | +3 |
| 신규 기능 | +2 |
| 아키텍처 결정 | +3 |
| 보안/인증/결제 | +4 |
| DB 스키마 변경 | +3 |

추측 금지. 모호 시 한 줄 질문.

3. Tier 분기 (**fail-loud, 자동 다운그레이드 금지**):
   - 0–3 → Tier 1 진행
   - 4+ → 채팅에 다음 출력 후 사용자 답변 대기:
     ```
     complexity=<X> → Tier <N>. MVP는 Tier 1(≤3)만 지원.
     (a) 강제 Tier 1으로 진행 (위험: 단순화로 인한 누락 가능)
     (b) 중단 + lessons.md에 "범위 초과" entry 기록 후 사용자 재설계 권유
     ```

4. **state.json 갱신**:
   ```json
   {
     "current_phase": "classify",
     "tier": 1,
     "complexity_score": 3,
     "score_breakdown": { ... },
     "completed_phases": ["classify"]
   }
   ```

5. **사용자 확인** — **[승인 2]**:
   ```
   Tier 1 / complexity=<X>. Brainstorm phase 진입할까요?
   기본 호출: superpowers:brainstorming (config.yaml.phases.brainstorm)
   ```

---

## Phase 2 — Brainstorm

### 단계

1. `config.yaml`의 `phases.brainstorm` 읽기 (기본: `type: skill, id: superpowers:brainstorming`)

2. `type` 분기:

| `type` | 동작 |
|--------|------|
| `skill` | `Skill(<id>)` 호출 |
| `command` | 사용자에게 "다음 슬래시 명령을 직접 실행해주세요: `<value>`" 안내 |
| `inline` | `<path>` Read 후 가이드 따라 직접 진행 |

3. **실패 처리**:
   - Skill 호출 결과가 명백히 실패 (스킬 미존재, 에러) → `fallback` 경로의 inline 가이드로 자동 전환
   - 채팅에 명시: "외부 스킬 실패 → fallback 가이드로 진행 (references/phase-guides.md#brainstorm)"

4. **state.json 갱신**:
   ```json
   { "current_phase": "brainstorm", "completed_phases": [..., "brainstorm"] }
   ```

5. **[승인 없음]** — superpowers brainstorming 자체가 사용자 디자인 승인 단계를 포함. Plan phase 자동 진입.

---

## Phase 3 — Plan

### 단계

1. `config.yaml`의 `phases.plan` 읽기 (기본: `type: skill, id: superpowers:writing-plans`)

2. Phase 2와 동일한 `type` 분기로 위임

3. **state.json 갱신**:
   ```json
   { "current_phase": "plan", "completed_phases": [..., "plan"] }
   ```

4. **사용자 확인** — **[승인 3]** (Execute = 코드 변경 직전, 가장 중요한 분기점):
   ```
   Plan 작성 완료. Execute phase 진입할까요?
   기본 호출: superpowers:executing-plans
   ⚠️ 이 단계부터 실제 코드 변경이 발생합니다.
   ```

---

## Phase 4 — Execute

### 단계

1. `config.yaml`의 `phases.execute` 읽기 (기본: `type: skill, id: superpowers:executing-plans`)

2. 동일한 `type` 분기로 위임

3. **git 가능 시 safe 태그**:
   ```bash
   git tag safe/exec-$(date +%Y%m%d-%H%M%S)
   ```
   state.json `last_safe_tag`에 태그명 기록

4. **non-git** → 태그 스킵 + warning: "git repo가 아니므로 롤백 보장 없음"

5. **state.json 갱신**:
   ```json
   {
     "current_phase": "execute",
     "completed_phases": [..., "execute"],
     "last_safe_tag": "safe/exec-..."
   }
   ```

6. **[승인 없음]** — QA 자동 진입

---

## Phase 5 — QA

### 단계

1. `config.yaml`의 `phases.qa` 읽기 (기본: `type: skill, id: qa`)

2. 동일한 `type` 분기로 위임

3. **결과 분기**:
   - **PASS** → state.json `completed_phases += "qa"` → Phase 6 진입
   - **FAIL** → state.json:
     ```json
     {
       "current_phase": "blocked",
       "blocked_reason": "qa_failed"
     }
     ```
     사용자에게:
     ```
     QA 실패. 다음 중 선택:
     (a) Execute 재진입 — 문제 수정 후 재실행
     (b) Lesson 기록 후 종료 — 현재 상태를 학습 기록으로 남기고 중단
     ```

4. **사용자 확인** — **[승인 4]** (PASS인 경우):
   ```
   QA 통과. Lesson 기록 단계로 진입할까요?
   ```

---

## Phase 6 — Lesson

### 단계

1. `references/lesson-template.md` Read

2. 이번 파이프라인 결과를 템플릿 형식으로 작성:
   - 날짜·시간 (ISO 8601)
   - Tier, Complexity
   - Outcome (`done` 또는 `blocked`)
   - User request 요약
   - Context, Pattern, Solution, Rule

3. **lessons.md append**:
   - `<root>/.harness/lessons.md` 존재 시 → 파일 끝에 `\n---\n\n<new entry>` append
   - 부재 시 → 새 파일로 entry 작성

4. **state.json 최종 갱신**:
   ```json
   {
     "current_phase": "done",
     "finished_at": "<ISO-8601 now>",
     "completed_phases": [..., "lesson"]
   }
   ```
   실패 종료 시: `current_phase: "blocked"` 유지, `blocked_reason` 유지

5. **최종 요약 출력**:
   ```
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   ✅ dev-harness 완료

   Tier: 1 / Complexity: 3
   Phases: classify → brainstorm → plan → execute → qa → lesson
   Safe tag: safe/exec-...
   Lesson entry: 1개 append됨

   다음 세션에서 이 lesson이 자동 재투입됩니다.
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   ```

---

## Phase 7 — Resume (Phase 0 분기 처리)

`state.json.current_phase` 가 `idle`/`done`이 아니면 진입.

### 단계

1. 사용자에게 안내:
   ```
   이전 세션의 dev-harness가 Phase <X>에서 중단됨.
   (상태: <current_phase>, blocked_reason: <reason or null>)
   이어서 진행할까요? (Y/n)
   ```

2. **lessons.md 재투입 반드시 다시 수행** (Phase 0 step 3과 동일):
   - verbatim 인용 + 능동 제약 선언 한 줄

3. `completed_phases`의 마지막 항목 다음 phase부터 재개:
   - 예: `completed_phases: ["classify", "brainstorm"]` → Phase 3 (Plan)부터

4. `current_phase`를 재개 phase로 갱신

---

## 공통 룰

### 단계 위반 금지

- 사용자 승인 지점(`[승인 X]`)에서 답변 전에 다음 phase 진행 금지
- Skill/Command 호출 결과를 받지 않은 채 state.json `completed_phases` append 금지
- Phase 순서 건너뛰기 금지 (예: Classify → Execute 직행)

### 재투입된 lesson 우선

- Phase 0에서 인용된 lesson의 Rule들은 본 SKILL.md의 가이드보다 **우선 적용**
- 충돌 시 lesson Rule 따르고, 사용자에게 "lesson rule '<rule>'을 적용했음" 명시

### state.json 일관성

- 각 phase 시작 시 `current_phase` 갱신
- 각 phase 완료 시 `completed_phases` append
- 실패 시 `current_phase: "blocked"` + `blocked_reason` 설정 (덮어쓰기 금지, append 금지)

### type: command 한계

- Claude는 슬래시 커맨드를 직접 실행 못 함
- `type: command` 매핑은 사용자에게 "다음을 직접 실행해주세요: `<value>`" 안내 후 사용자 응답 대기
- 사용자가 결과를 보고한 뒤에야 다음 단계 진행
