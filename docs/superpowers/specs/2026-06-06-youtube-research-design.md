# `youtube-research` 스킬 설계

- **날짜**: 2026-06-06
- **상태**: 설계 승인됨 (구현 전)
- **스킬 위치**: `youtube-research/` (claude-skills 워크스페이스 루트)

## 1. 목적 (Purpose)

사용자가 **토픽**을 던지면, 유튜브 영상들에서 정보를 수집·정제하고, 핵심 주장을 웹으로 **팩트검증**한 뒤, **사실에 근거한 최종 정리 마크다운**을 생성하는 스킬.

기존 `youtube-study-notes`가 "영상 1개 → 학습노트"라면, 이 스킬은 **"토픽 → 다중 영상 수집 → 팩트검증 → 리서치 정리"** 다. 단순 요약기가 아니라 **검증된 사실**을 산출하는 게 차별점이다.

### 비목표 (Non-goals)

- 영상 다운로드·화질/음성 추출 (자막만 다룬다)
- 단일 영상 학습노트 (그건 `youtube-study-notes` 영역)
- 모든 주장 전수 검증 (핵심 주장만 선별 검증 — 토큰 경제)

## 2. 설계 결정 요약

| 축 | 결정 | 근거 |
|---|---|---|
| 입력 | 사용자가 URL/채널 제공 + **선별 메모리**로 결정 누적 → 하이브리드 → 자동 졸업 | 품질은 사용자 큐레이션이 최고, 단 반복을 학습으로 줄임 |
| 검증 | 핵심 주장 선별 검증 + confidence 등급(✅/⚠️/❌) + 충돌 시 병기 | "사실 근거"의 실체. 전수검증은 토큰 과다 |
| 산출 | 워크스페이스 `research/<토픽>/` 자기완결 | obsidian 의존 없이 독립, 핸드오프는 선택적 |
| 아키텍처 | **C. 하이브리드** — 정제는 `dedup_subs.py` 재사용, 검증은 `deep-research` 호출 + 인라인 폴백 | 강점 흡수 + 약결합. `dev-harness`에서 검증된 패턴 |

## 3. 파이프라인 (6단계, 각 단계 독립 유닛)

각 단계는 **하나의 명확한 책임**을 갖고, 잘 정의된 입출력으로 통신하며, 독립적으로 이해·테스트 가능하다.

| # | 단계 | 입력 → 출력 | 구현 방식 |
|---|---|---|---|
| 1 | **선별 (Select)** | 토픽 + `.curation-log` → 확정 영상 목록 | 신규 (선별 메모리) |
| 2 | **수집·정제 (Collect)** | URL 목록 → 영상별 정제 `.txt` | `dedup_subs.py` 복사 재사용 |
| 3 | **주장 추출 (Extract)** | `.txt`들 → 교차병합된 핵심 주장 top-N | 신규 |
| 4 | **검증 (Verify)** | 주장 목록 → confidence + 출처 | `deep-research` 호출 + 인라인 폴백 |
| 5 | **합성 (Synthesize)** | 검증 결과 → 사실근거 최종 md | 신규 |
| 6 | **산출 (Output)** | → `research/<토픽>/` 저장 + 로그 갱신 | 신규 |

### 3.1 선별 (Select)

1. `research/.curation-log.md`를 읽어 이 토픽/도메인에 신뢰 채널이 있는지 확인
2. 졸업 단계(§4)에 따라:
   - *수동*: 사용자에게 영상 URL/채널 목록을 요청
   - *하이브리드*: 신뢰 채널에서 `yt-dlp "ytsearchN:<토픽>"`로 후보를 뽑아 표(제목·채널·길이·조회수)로 제시 → 사용자가 체크/추가/제외
   - *자동*: 후보 자동 선별 후 최종 확인 1회만
3. 확정된 각 영상의 accept/reject 결정을 `.curation-log`에 기록 (§4 스키마)
4. **상한**: 1회 실행당 영상 기본 ≤5개 (사용자 override 가능)

### 3.2 수집·정제 (Collect)

`youtube-study-notes`의 추출 로직을 상속한다:

- 전제: `yt-dlp` 설치, 멤버십·로그인 영상은 `--cookies-from-browser chrome`
- 추출: `--write-auto-subs --write-subs --skip-download --convert-subs srt`, 한국어 `ko` 우선
- 정제: 복사해 둔 `scripts/dedup_subs.py`로 prefix-dedup (라이브 누적자막 ~5배 압축, 타임스탬프 보존)
- 결과: 영상별 `evidence/<영상>.txt`
- **무자막 영상**: 사용자에게 알리고 옵션 제시(중단 / whisper 전사). 임의 진행 금지

### 3.3 주장 추출 (Extract)

1. 각 정제 `.txt`를 읽어 **선언적·검증가능 주장**을 추출
2. **주장 필터** = 다음 3조건을 모두 만족:
   - **중심성**: 토픽의 핵심에 닿는가
   - **반증가능성**: 사실/수치/인과/사실로 제시된 권고 (의견·취향·감상 제외)
   - **비자명성**: 상식이 아닌 것
3. 영상 간 **교차 병합·중복 제거** (여러 영상이 같은 주장을 하면 1개로, 출처는 모두 보존)
4. 결과: 출처 영상 + 타임스탬프가 붙은 주장 목록
5. **상한**: 토픽당 검증 대상 주장 기본 ≤12개 (병합 후 상위)

### 3.4 검증 (Verify)

- 핵심 주장 목록(≤12개)을 `config.yaml`의 `verify` phase 정의대로 검증:
  - `type: skill, id: deep-research` — 호출 (적대적 검증·인용 수집은 deep-research의 책임)
  - 호출 실패 시 `fallback: references/verify-inline.md`로 자동 전환
- **배칭**: 주장 1개당 1호출(최대 12회)이 아니라, **주장 목록 전체를 1회(또는 소수) 호출**로 묶어 넘긴다 — 토큰 상한을 지키기 위함. deep-research가 내부에서 주장별로 fan-out 검증
- deep-research 판정을 **confidence 루브릭**으로 매핑 (§5)
- 각 주장에 confidence 등급 + 근거 출처 URL 부착
- "사실" 출처 우선순위: 1차·공식·표준·학술 > 보도 > 블로그

### 3.5 합성 (Synthesize)

검증 결과를 **사실에 근거한 최종 마크다운**으로 재구성:

- **구조**: 토픽 개요 → confidence별 주장 정리(✅ 먼저) → 충돌/논쟁 지점 별도 → 인용·출처
- **충돌 처리**: 영상 주장과 사실이 다르면 양쪽 병기 + 정정 (영상 주장을 숨기지 않는다)
- **결론부터** 원칙: 빌드업은 압축, 핵심 명제를 앞에
- 각 주장 옆에 confidence 배지(✅/⚠️/❌)와 출처 링크

### 3.6 산출 (Output)

```
research/<토픽>/
  <토픽>-정리.md          ← 최종 산출물
  evidence/
    <영상>.txt            ← 정제 자막 (타임스탬프 보존, 재참조용)
    claims.md             ← 주장–출처–검증 매핑 테이블
research/.curation-log.md  ← 선별 메모리 (글로벌, 누적)
```

- 최종 결과를 사용자에게 표로 짧게 보고 (토픽, 영상 수, 검증 주장 수, ✅/⚠️/❌ 분포, 경로)
- **선택적 핸드오프**: 사용자가 원하면 `obsidian-capture`로 최종 노트를 2ndMe vault에 넘김 (기본은 안 함)

## 4. 선별 메모리 (Curation Memory) — 시그니처 기능

`research/.curation-log.md` (워크스페이스 글로벌, 마크다운). 사용자의 큐레이션 결정을 누적해 스킬을 **수동 → 하이브리드 → 자동**으로 졸업시킨다.

### 4.1 스키마

상단에 채널 신뢰 롤업 테이블:

```markdown
## 채널 신뢰도
| 채널 | accept | reject | 신뢰 상태 |
|---|---|---|---|
| 쉬운코드 | 5 | 0 | 신뢰(자동 후보) |
```

이어서 결정 로그 (1행 = 1결정):

```markdown
## 결정 로그
| 날짜 | 토픽 | 채널 | 영상제목 | URL | 결정 | 사유 |
|---|---|---|---|---|---|---|
| 2026-06-06 | GC 튜닝 | 쉬운코드 | ... | https://... | accept | 깊이 있고 검증됨 |
```

### 4.2 졸업 트리거 (숫자로 고정 — `config.yaml`에서 조정 가능)

| 단계 | 해금 조건 | 동작 |
|---|---|---|
| **수동** (기본) | — | 사용자가 URL 제공 |
| **하이브리드** | 한 채널 `accept ≥3 AND reject ≤1` | 새 토픽에서 그 채널 후보를 선제안, 사용자가 취사선택 |
| **자동** | 도메인에 신뢰 채널 ≥3개 AND 스킬 제안 accept율 ≥80% (최소 5회 제안) | 후보 자동 선별 → 최종 확인 1회만 |

- 트리거 상수는 `config.yaml`의 `curation:` 블록에 노출 (예: `trust_accept_threshold: 3`)
- 자동 단계에서도 사용자는 항상 최종 confirm 또는 거부 가능 (거부 시 reject로 기록되어 신뢰도 하향)

## 5. Confidence 루브릭

| 등급 | 조건 |
|---|---|
| ✅ 확인 | 독립 권위 출처 ≥2개가 일치 |
| ⚠️ 논쟁·불확실 | 출처 간 상충 OR 단일 출처만 존재 OR 강하게 맥락 의존 |
| ❌ 반증 | 권위 출처가 주장을 명확히 반박 |

- 적대적 검증(서로 다른 관점으로 주장을 반증 시도)은 **`deep-research`에 위임**. 이 스킬은 루브릭을 재발명하지 않고 deep-research 판정을 위 등급으로 매핑한다.
- 웹도 틀릴 수 있으므로 출처 권위 순위(1차·공식·표준·학술 > 보도 > 블로그)를 deep-research 호출 프롬프트에 명시한다.

## 6. 아키텍처 / 재사용 메커니즘

`dev-harness`에서 검증된 패턴을 차용: `config.yaml`이 단계를 외부 스킬에 매핑하고, 호출 실패 시 인라인 폴백으로 자동 전환.

```yaml
# youtube-research/config.yaml (발췌)
verify:
  type: skill
  id: deep-research
  fallback: references/verify-inline.md

curation:
  max_videos_per_run: 5
  max_claims_per_run: 12
  trust_accept_threshold: 3
  trust_reject_ceiling: 1
  auto_min_channels: 3
  auto_accept_rate: 0.8
  auto_min_suggestions: 5
```

### 재사용 결정 (드리프트 vs 결합)

| 자산 | 방식 | 근거 |
|---|---|---|
| `dedup_subs.py` | **복사** (`scripts/`로) | 안정된 유틸, 드리프트 위험 낮음. 자기완결 산출 철학과 일치 |
| yt-dlp·쿠키·무자막 처리 | **상속(복사)** from youtube-study-notes | 전제·트러블슈팅을 조용히 누락하지 않기 위함 |
| `deep-research` | **런타임 호출** (config 매핑) | 정교한 검증을 매번 호출. 변경이 자동 반영 |

## 7. 스킬 파일 구성

```
youtube-research/
  SKILL.md                       ← description + 6단계 워크플로
  config.yaml                    ← verify phase 매핑 + curation 상수
  scripts/
    dedup_subs.py                ← youtube-study-notes에서 복사
  references/
    verify-inline.md             ← deep-research 미존재 시 폴백 (짧은 가이드)
    curation-schema.md           ← .curation-log 스키마·졸업 로직 상세
```

## 8. 에러 처리 / 트러블슈팅 (상속)

| 증상 | 처리 |
|---|---|
| `could not copy cookies` | Chrome 실행 중 → 완전 종료 후 재시도 |
| `Sign in to confirm you're not a bot` | 쿠키 만료 → `--cookies-from-browser chrome:Default` |
| 자막 0바이트 | 영상에 자막 없음 → whisper 전사 옵션 안내, 임의 진행 금지 |
| `deep-research` 호출 실패 | `references/verify-inline.md` 폴백으로 자동 전환 |
| 영상 0개 확정 | 사용자에게 URL 재요청, 파이프라인 진행 안 함 |

## 9. YAGNI / 범위 통제

- **v1 검증 폴백**은 짧은 인라인 가이드(WebSearch 몇 개 + 합의 체크)만. deep-research 전체 재구현 ❌
- 토큰 상한(영상 ≤5, 주장 ≤12)을 기본값으로 박아 deep-research 호출 비용을 묶는다
- 선별 메모리는 단일 마크다운 파일. DB·인덱스 도입 ❌ (필요해지면 그때)
- Obsidian 연동은 선택적 핸드오프만. 스킬 본체는 vault에 의존하지 않는다

## 10. 성공 기준

1. 토픽 + 영상 URL 몇 개를 주면 `research/<토픽>/<토픽>-정리.md`가 생성된다
2. 최종 md의 각 핵심 주장에 confidence 배지와 출처 링크가 붙어 있다
3. 영상 주장과 웹 사실이 충돌하면 양쪽이 병기된다
4. 선별 결정이 `.curation-log.md`에 누적된다
5. 같은 신뢰 채널이 임계치를 넘으면 다음 토픽에서 후보를 선제안한다 (하이브리드 졸업)
6. `deep-research`가 없는 환경에서도 인라인 폴백으로 검증이 동작한다
