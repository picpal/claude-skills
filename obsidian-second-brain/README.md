# Obsidian 제2의 뇌 Pack

이 pack은 Obsidian Vault를 제2의 뇌처럼 운용하기 위한 스킬, 공통 레퍼런스, 템플릿, 실행 도구를 묶습니다.

목표는 단순 저장소가 아니라, 자료와 생각이 들어올 때마다 기존 지식과 비교되고, 링크되고, 프로젝트와 의사결정으로 이어지는 "컴파일된 기억층"을 만드는 것입니다.

## 한눈에 보는 흐름

```text
init
  -> capture
  -> compile
  -> retrieve
  -> lint/review
  -> 다시 capture
```

- `obsidian-init`: Vault를 사용할 수 있는 상태로 초기 세팅하고 연결을 검증합니다.
- `obsidian-capture`: 생각, 링크, CLI 대화, OCR 책, 문서, 이미지, 영상, 웹페이지를 빠르게 받아 적습니다.
- `obsidian-compile`: 쌓인 자료를 기존 노트와 비교해 개념, 주장, 질문, 인사이트, 프로젝트, 의사결정으로 재구성합니다.
- `obsidian-retrieve`: 질문에 대해 Vault 안의 지도, 객체, 원본 근거를 따라가며 답을 가져옵니다.
- `obsidian-lint`: 오래된 주장, 끊어진 링크, 중복 개념, 방치된 질문, 검토 필요한 결정을 찾아 정리합니다.

## 구성

- `skills/`: Codex가 직접 호출하는 Obsidian 관련 스킬.
- `shared/obsidian-second-brain/`: 이 pack 내부 스킬들이 공유하는 노트 타입, 워크플로우, 신뢰성 규칙, 템플릿.
- `tools/`: Vault 초기화와 pack 검증 스크립트.
- `vault-template/`: 실제 Obsidian Vault에 복사되는 초기 구조.

## 포함 스킬

- `obsidian-init`
- `obsidian-capture`
- `obsidian-compile`
- `obsidian-retrieve`
- `obsidian-lint`

## 빠른 시작

### 1. Claude Code에 스킬 등재

심볼릭 링크로 사용자 레벨에 등재합니다 (각 sub-skill을 개별 등록).

```bash
# claude-skills 루트 기준 — 이 pack을 claude-skills/obsidian-second-brain/ 에 둔 경우
PACK="$PWD/obsidian-second-brain"
for skill in obsidian-init obsidian-capture obsidian-compile obsidian-retrieve obsidian-lint; do
  ln -sf "$PACK/skills/$skill" "$HOME/.claude/skills/$skill"
done
```

등재 후 새 Claude Code 세션을 열면 Skill tool이 description 키워드를 매칭해 다음 5개를 자동으로 발동할 수 있습니다.

```text
obsidian-init
obsidian-capture
obsidian-compile
obsidian-retrieve
obsidian-lint
```

검증은 pack 루트에서 다음 스크립트로 합니다.

```bash
./tools/verify-second-brain-skills.sh
```

### 2. Vault 초기화

이미 쓰는 Obsidian Vault가 있어도 초기화는 비파괴 방식입니다. 없는 폴더와 템플릿만 만들고, 기존 노트는 덮어쓰지 않습니다.

```bash
# pack 루트에서
./tools/init-second-brain-vault.sh /path/to/obsidian-vault
./tools/verify-vault.sh /path/to/obsidian-vault
```

초기화 후 주요 시작점은 다음과 같습니다.

- `00_System/dashboards/Home.md`: 현재 지식 상태, 처리 대기, 리뷰 항목을 보는 홈.
- `10_Capture/inbox/`: 오늘 생각, 아이디어, 짧은 메모가 먼저 들어오는 곳.
- `10_Capture/unprocessed/`: 아직 의미 분류가 애매한 자료.
- `20_Sources/`: 원본 자료 보관층. 세션, 웹, 영상, 이미지, 책, 논문, 문서 등.
- `30_Objects/`: 개념, 주장, 질문, 인사이트 같은 지식 객체.
- `40_Maps/`: 토픽별 지도. 관련 객체와 원본을 탐색하는 입구.
- `50_Execution/`: 프로젝트와 의사결정.
- `60_Reviews/`: 점검 보고서와 주간 리뷰.

## 실제 사용법

### 아무 생각이나 넣기

분류를 먼저 고민하지 않아도 됩니다. 다음처럼 말하면 `obsidian-capture`가 원본을 보존하고 적절한 임시 위치에 저장합니다.

```text
/obsidian-capture
Vault는 /path/to/obsidian-vault 야.
오늘 든 생각: LLM 스킬은 단순 자동화가 아니라 나의 사고 루틴을 외부화하는 방식이어야 한다.
```

자료 종류별 기본 저장 위치는 다음과 같습니다.

- 빠른 생각과 아이디어: `10_Capture/inbox/`
- 애매한 자료: `10_Capture/unprocessed/`
- CLI 세션: `20_Sources/sessions/`
- 웹페이지와 링크: `20_Sources/web/`
- 영상 링크와 YouTube 자막 요약: `20_Sources/videos/`
- 이미지 참조: `20_Sources/images/`
- OCR PDF, 스캔 PDF, OCR 원문 파일: `20_Sources/books/raw/`
- 책 인덱스, 장/절 Source, 책 발췌: `20_Sources/books/`
- 논문과 리포트: `20_Sources/papers/`
- 문서와 PDF: `20_Sources/documents/`

YouTube나 영상 링크는 단순 URL 저장으로 끝내지 않습니다. 자막, 스크립트, 캡션, 사용자가 붙여준 transcript가 있으면 그 텍스트를 근거로 요약, 핵심 주장, timestamp note, compile 후보를 함께 남깁니다.

```text
/obsidian-capture
이 YouTube 링크를 영상 Source로 저장해줘.
가능하면 자막/스크립트 기준으로 핵심 내용, timestamp note, concept/claim/question/insight 후보까지 정리해줘.
https://www.youtube.com/watch?v=...
```

자막이나 스크립트에 접근할 수 없으면 `status: needs_transcript`로 저장하고, 제목이나 썸네일만 보고 내용을 추측하지 않습니다.

OCR 책 원본은 `20_Sources/books/raw/`에 둡니다. 책 전체가 길다면 한 파일에 몰아넣지 않고, `20_Sources/books/`에 책 단위 인덱스와 장/절 단위 Source를 따로 만듭니다.

```text
/obsidian-capture
이 OCR 책 파일을 book Source로 저장해줘.
책 전체 인덱스와 장별 요약, 위치 메모, concept/claim/question/insight 후보를 만들어줘.
20_Sources/books/raw/book-ocr.pdf
```

OCR 품질이 낮거나 페이지 경계가 불확실하면 `status: needs_ocr_review`로 남기고, 확실하지 않은 OCR 문장을 강한 근거처럼 다루지 않습니다.

### 쌓인 자료를 지식으로 바꾸기

`capture`는 저장, `compile`은 사고 정리입니다. 캡처된 자료가 어느 정도 쌓였거나 중요한 생각이 들어왔을 때 실행합니다.

```text
/obsidian-compile
최근 inbox와 web 자료를 기존 AI/LLM 관련 노트와 비교해서 개념, 질문, 인사이트, 프로젝트 액션으로 정리해줘.
```

`compile`은 다음 순서로 움직입니다.

1. 원본 자료와 캡처 노트를 확인합니다.
2. 관련 `40_Maps`와 `30_Objects`를 먼저 읽습니다.
3. 기존 노트를 업데이트할지, 새 객체 노트를 만들지 판단합니다.
4. 의미 있는 연결, 모순, 반복 패턴, 실행 함의가 있을 때만 `Insight`를 만듭니다.
5. 관련 지도, 프로젝트, 의사결정, 로그를 갱신합니다.

### Vault에 질문하기

이미 축적된 자료에서 답을 얻고 싶을 때는 `obsidian-retrieve`를 사용합니다.

```text
/obsidian-retrieve
내 Vault 기준으로 "Codex와 Claude 스킬 구조를 어떻게 분리해야 하는가?"에 답해줘.
근거 링크와 추론을 나눠서 보여줘.
```

답변은 원칙적으로 다음 층을 따라갑니다.

```text
40_Maps -> 30_Objects -> 20_Sources
```

즉, 토픽 지도에서 시작해서 개념, 주장, 질문, 인사이트를 따라가고, 마지막에 원본 근거를 확인합니다. 근거가 약하면 `confidence: low` 또는 `needs_evidence`로 남겨야 합니다.

### 정기적으로 건강검진하기

자료가 많아질수록 방치된 질문, 중복 개념, 오래된 결정이 생깁니다. 이때 `obsidian-lint`를 실행합니다.

```text
/obsidian-lint
Vault 전체를 점검해서 중복 개념, 끊어진 링크, 오래된 주장, 검토 필요한 결정을 보고서로 만들어줘.
```

보고서는 `60_Reviews/lint-reports/`에 저장되며, 직접 대규모 삭제나 자동 병합을 하지 않습니다. 제안 목록을 만든 뒤 사용자가 승인하는 방식으로 정리합니다.

## 추천 운영 루틴

### 매일

- 떠오른 생각, 링크, 대화, 작업 로그를 `obsidian-capture`로 넣습니다.
- 분류가 애매하면 그냥 `inbox`나 `unprocessed`로 둡니다.
- 중요한 작업이 끝났다면 CLI 세션 요약을 `20_Sources/sessions/`에 남깁니다.

### 주 1회

- `obsidian-compile`로 최근 캡처를 지식 객체와 지도에 연결합니다.
- 새로 생긴 인사이트를 프로젝트와 의사결정에 연결합니다.
- `60_Reviews/weekly/`에 주간 리뷰를 남깁니다.

### 월 1회 또는 자료가 많아졌을 때

- `obsidian-lint`로 Vault 건강 상태를 점검합니다.
- 중복 개념, 방치된 질문, 오래된 결정, 근거 약한 주장을 정리합니다.
- Home 대시보드가 실제로 다시 보고 싶은 화면인지 확인합니다.

## 노트 타입 역할

- `Source`: 원본 자료. 링크, 영상, 세션, OCR 책, 문서, 이미지, 웹페이지.
- `Concept`: 반복해서 등장하는 개념.
- `Claim`: 참/거짓 또는 강약을 검토해야 하는 주장.
- `Question`: 아직 답이 없거나 더 조사해야 하는 질문.
- `Insight`: 여러 자료가 연결되며 새로 생긴 해석, 패턴, 실행 함의.
- `Map`: 특정 주제의 탐색 지도.
- `Project`: 실행 중이거나 실행 후보인 작업.
- `Decision`: 선택지, 근거, 결정, 재검토 시점을 기록하는 노트.

자세한 규칙은 `shared/obsidian-second-brain/references/note-types.md`와 `shared/obsidian-second-brain/references/workflows.md`를 참고합니다.

## 좋은 사용 예시

```text
/obsidian-capture
이 링크 저장해줘. 나중에 AI 에이전트 구조 설계와 연결될 수 있어.
https://example.com/article
```

```text
/obsidian-compile
최근 캡처된 AI 에이전트 관련 자료를 기존 Claude, Codex, Obsidian second brain 노트와 비교해서 인사이트만 뽑아줘.
```

```text
/obsidian-retrieve
내가 왜 Obsidian과 Notion을 분리해서 쓰려고 했는지 근거 노트 기준으로 요약해줘.
```

```text
/obsidian-lint
AI/LLM 지도에서 오래된 주장과 근거 없는 결론을 찾아줘.
```

## 실패하지 않기 위한 원칙

- 저장할 때는 가볍게, 정리할 때는 신중하게 합니다.
- 원본 자료는 절대 덮어쓰지 않습니다.
- 확신이 없으면 `Question`이나 `hypothesis`로 남깁니다.
- 너무 긴 단일 노트보다 작은 객체 노트와 지도 링크를 선호합니다.
- 인사이트는 새 연결, 모순, 반복 패턴, 실행 함의가 있을 때만 만듭니다.
- 프로젝트와 의사결정으로 이어지지 않는 지식은 주기적으로 다시 묶거나 보관합니다.

## Pack 검증

```bash
packs/obsidian-second-brain/tools/verify-second-brain-skills.sh
```

성공 시 출력:

```text
Second brain skill pack verification passed.
```
