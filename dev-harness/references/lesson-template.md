# Lesson Template

Phase 6 (Lesson)에서 lessons.md에 append할 entry 형식.

## 템플릿

```markdown
## YYYY-MM-DD HH:MM — <요약 한 줄>

**Tier:** 1
**Complexity:** <score>
**Outcome:** done / blocked
**User request:** <원문 요약, 40자 이내>

### Context
<무엇을 하려 했는지. 1-3문장>

### Pattern (재발 가능한 형태)
<일반화된 상황 패턴. "X 할 때 Y가 발생하는 경향" 식으로>

### Solution
<구체적 해결 방법. 사용한 외부 스킬, 핵심 명령, 도구>

### Rule (향후 능동 제약)
<다음 세션에서 따를 한 줄 규칙. 이게 lessons.md의 진짜 자산>

---
```

## 작성 가이드

- **요약 한 줄**: H2 헤더에 핵심 결과 (예: "slugify 함수 추가 / 통과")
- **Outcome**: `done` (정상 완료) / `blocked` (QA 실패 또는 사용자 중단)
- **Pattern**: 이번 작업이 아닌 **재발 가능한 형태**로 추상화. "단일 유틸 함수 + 신규 모듈"처럼 다음 세션에서 매칭할 수 있어야 함
- **Rule**: 다음 세션에서 Phase 0이 verbatim 인용했을 때 **능동 제약**으로 작동해야 함. 행동 가능한 명령형으로 작성
  - 좋은 예: "DB 변경 동반된 PR은 마이그레이션 스크립트도 함께 작성한다"
  - 나쁜 예: "주의해야 한다" (모호함)

## Append 방식

`<root>/.harness/lessons.md`에 다음 순서로 추가:
1. 파일 존재 시 → Bash로 `cat >> lessons.md` 또는 Read → 전체 재작성
2. 파일 부재 시 → 첫 entry로 생성

새 entry는 항상 **파일 끝**에 append. 최신 entry가 가장 아래에 위치 (Phase 0에서 `---` 기준 마지막 5개를 추출하는 로직과 일치).

## 실패 케이스 (Outcome: blocked)

```markdown
## 2026-05-14 14:30 — auth middleware 추가 / QA 실패 중단

**Tier:** 1
**Complexity:** 3
**Outcome:** blocked
**User request:** auth middleware 추가

### Context
세션 토큰 검증 미들웨어 추가 시도. QA에서 토큰 만료 케이스 누락 발견.

### Pattern (재발 가능한 형태)
인증 관련 작업은 만료/갱신/리프레시 케이스를 항상 동반함.

### Solution
이번 세션에서는 미완. 사용자가 만료 케이스 설계 후 재시작 결정.

### Rule (향후 능동 제약)
인증 관련 작업은 plan phase에서 "만료/갱신/리프레시 3가지 케이스 모두 처리됨?" 명시 확인한다.

---
```
