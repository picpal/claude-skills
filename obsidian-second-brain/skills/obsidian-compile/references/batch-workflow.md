# Batch Compile Workflow

`obsidian-compile` Batch Mode의 상세 명세. SKILL.md의 "Batch Mode" 섹션 보강.

## Trigger Phrases

다음 표현이 들어오면 단일 노트 compile 대신 batch 진입:

- "compile inbox", "auto compile", "batch compile"
- "캡처된 자료 전부 정리", "쌓인 거 다 컴파일", "inbox 비워줘"
- 인자 없는 `obsidian-compile` 호출 + `10_Capture/inbox/`에 `status: captured` 노트 ≥ 2개

단일 파일 경로가 인자로 주어지면 batch 진입하지 않고 기존 single-note workflow로.

## Collection Query

```
glob: 10_Capture/inbox/**/*.md
glob: 10_Capture/unprocessed/**/*.md
glob: 20_Sources/**/*.md
```

각 노트의 frontmatter `status` 값으로 분류:

| status | 동작 |
|---|---|
| `captured` | PROCESS |
| `needs_classification` | PROCESS (분류는 compile이 결정) |
| `needs_transcript` | SKIP — 리포트만 |
| `needs_ocr_review` | SKIP — 리포트만 |
| `compiled` / `processed` | SKIP — 이미 처리 |
| 없음 | PROCESS (legacy 캡처) |

추가 필터:
- 마지막 수정 시각이 **5분 이내**면 SKIP (capture 진행 중 가능성).
- 파일 크기 > 100KB면 SKIP & 별도 알림 (수동 분할 필요).

## Processing Order

```
1. source_type: web, document, paper     # 정제 텍스트 — 가장 안전
2. source_type: cli_session              # 구조화된 로그
3. source_type: thought, note            # 사용자 본인 정리
4. source_type: video (transcript 있음)  # 자막 기반
5. source_type: book (review 완료)       # OCR — 가장 노이즈 많음
```

같은 카테고리 내에서는 `created` 오래된 순. 신뢰도 높은 노트가 먼저 처리되어야 뒤 노트들이 더 풍부한 vault 컨텍스트에서 compile됨.

## Dry-run Preview Format

```
Batch Compile Preview — {{vault_path}}
═══════════════════════════════════════
PROCESS: {{N}}개

[1] 10_Capture/inbox/2026-05-19-llm-wiki.md  (source_type: web)
    후보: Concept "LLM Wiki pattern", Question "RAG vs pre-compile tradeoff"
    매칭: [[obsidian-second-brain]] (Map), [[ai-knowledge-base]] (Concept)
    계획:
      - update [[ai-knowledge-base]] (+ Key Point, + Source link)
      - update [[obsidian-second-brain]] (+ Tensions 한 줄)
      - create Question "RAG vs pre-compile tradeoff" (status: open)
      - Insight candidate: "Karpathy LLM Wiki = 사용자 capture/compile의 부분집합"

[2] 20_Sources/videos/2026-05-18-talk.md  (source_type: video)
    ...

SKIP: {{M}}개
    - 20_Sources/books/raw/book-x.md  (needs_ocr_review)
    - 20_Sources/videos/yt-abc.md     (needs_transcript)
    - 10_Capture/inbox/draft.md       (수정 < 5분 전)

예상 작업: update {{X}}, create {{Y}}, insight candidate {{Z}}
진행할까요? (yes / no / select-only N1,N2,...)
```

## Auto-confirm 진입 조건

prompt에 다음 중 하나가 있으면 preview 건너뜀:
- "auto-confirm", "no preview", "그냥 돌려"
- 호출자가 `/schedule` 또는 `/loop` 컨텍스트로 식별됨

## Per-note Execution Rules

각 노트 처리는 [기본 compile-workflow](compile-workflow.md)를 따르되 다음 추가:

1. 시작 전: 소스 노트 frontmatter에 `compile_started_at: <ISO>` 마킹 (재시도 멱등성).
2. 끝나면: `status: compiled`, `compiled_at: <date>` 설정, `compile_started_at` 제거.
3. 실패: `status: compile_failed`, `compile_error: <message>` 마킹 후 다음 노트로 진행. **batch는 멈추지 않음.**
4. **Insight는 candidate만**: Batch Mode에서 자동 생성된 Insight는 `status: candidate`, `promoted: false`. 사람 검토 후 promote.

## Contradiction Handling

기존 Concept/Claim과 새 소스가 모순될 때:

- 기존 노트 본문은 **수정하지 않음**.
- 노트 끝에 callout 추가:
  ```markdown
  > [!warning] Contradiction
  > [[새소스]]에서 다음 주장: "..."
  > 기존 결론과 충돌. 검토 필요.
  ```
- Question 노트 생성: `이 모순을 어떻게 해소할 것인가?`, `status: open`, link both sides.

## Final Report

```
Batch Compile Done — {{date}}
═════════════════════════════
Processed: {{N}}
  Updated notes: {{X}}
  Created notes: {{Y}}
  Insight candidates: {{Z}} (사람 검토 대기)
Skipped: {{S}}
  needs_transcript: {{a}}
  needs_ocr_review: {{b}}
  recent edits: {{c}}
  oversized: {{d}}
Failed: {{F}}  (상세: 00_System/logs/batch-compile-{{date}}.md)

Pending action:
  - Insight candidates 확인: [[insight-A]], [[insight-B]]
  - Contradictions 생긴 Question: [[question-X]]
  - 다음 batch 권장: {{transcript_count}}건이 transcript 확보 대기 중

다음 자동 실행: {{scheduled_next}}  (있을 때)
```

## Log File Format

`00_System/logs/batch-compile-{{YYYY-MM-DD}}.md` — 같은 날 여러 번 돌면 append.

```markdown
# Batch Compile Log — 2026-05-19

## Run 1 — 14:32 KST
- Source: [[2026-05-19-llm-wiki]] → updated [[ai-knowledge-base]], created [[q-rag-vs-precompile]]
- Source: [[2026-05-18-talk]] → updated [[agent-orchestration]]
- Insight candidate: [[i-karpathy-vs-second-brain]]
- Skipped: 2 (needs_transcript), 1 (recent edit)
- Failed: 0

## Run 2 — 22:00 KST (scheduled)
...
```

## Limits

| 항목 | 기본값 | 비고 |
|---|---|---|
| Per-run 최대 처리 노트 수 | 20 | 초과분은 다음 run으로 |
| 노트당 최대 크기 | 100KB | 초과 시 skip |
| Recent edit 윈도우 | 5분 | capture 진행 중 회피 |
| Auto-promoted Insight | 0 | candidate만, promotion은 사람 |
| 실패 시 batch 중단 | No | per-note 격리 |

## What Batch Mode Will Not Do

- Map의 구조를 바꾸지 않음 (`## Tensions` 등 기존 섹션에 한 줄 추가만).
- Project/Decision 노트를 자동 생성하지 않음 — 이건 사람의 의도 표명이 필요.
- 기존 Insight를 수정하지 않음 — 새 evidence는 candidate로만.
- vault 외부에 어떤 파일도 쓰지 않음.
