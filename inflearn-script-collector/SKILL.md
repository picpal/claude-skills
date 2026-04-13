---
name: inflearn-script-collector
description: |
  인프런(Inflearn) 강의 스크립트를 Claude in Chrome을 통해 자동 수집하고,
  챕터별로 원본 스크립트 MD 파일과 내용 정리 MD 파일을 생성하는 스킬.
  이 스킬은 사용자가 인프런 강의 스크립트, 자막, 강의 노트, 강의 정리, 인프런 필기,
  수업 내용 추출 등을 요청할 때 반드시 사용한다.
  "인프런 강의 정리해줘", "이 강의 스크립트 뽑아줘", "인프런 수업 노트 만들어줘",
  "강의 내용 MD로 정리해줘", "인프런 자막 추출해줘" 같은 요청에 모두 트리거된다.
  인프런 URL이 포함된 메시지에서도 트리거된다.
---

# 인프런 강의 스크립트 수집 및 정리 스킬

인프런(inflearn.com) 강의 페이지에서 Claude in Chrome을 활용하여 강의 스크립트를 자동 수집하고, 두 가지 형태의 마크다운 파일을 생성하는 스킬이다.

## 생성 파일

각 챕터(강의 영상)마다 두 개의 MD 파일을 생성한다:

1. **`NN_제목_script.md`** — 타임스탬프 포함 원본 스크립트 그대로
2. **`NN_제목_notes.md`** — 핵심 개념별 소제목으로 구조화한 내용 정리

모든 파일은 `강의명/` 단일 폴더 안에 저장한다.

## 전제 조건

- **Claude in Chrome 확장 프로그램**이 설치되고 연결된 상태여야 한다.
- 사용자가 인프런에 **로그인**되어 있어야 스크립트 탭에 접근 가능하다.
- 강의에 **스크립트(자막)가 있는 강의**만 수집 가능하다.

## 핵심 기술 원리

### 왜 특별한 수집 방식이 필요한가

인프런 스크립트 패널에는 세 가지 기술적 장벽이 있다:

1. **가상 스크롤(Virtual Scroll)**: DOM에는 화면에 보이는 텍스트만 존재하며, 나머지는 스크롤 시 lazy-loading 됨
2. **비디오 자동 재생 간섭**: 비디오가 재생 중이면 스크립트 패널이 현재 재생 위치로 자동 스크롤되어, 수동 스크롤을 방해함
3. **JS 결과 크기 제한**: `javascript_tool`의 반환값에 글자 수 제한이 있어, 긴 스크립트를 한 번에 반환할 수 없음

### 해결 전략

1. **video.pause() + seek to end** → 자동 스크롤 간섭 제거 + 모든 스크립트 데이터 로딩
2. **Timestamp Map 기반 수집** → 초(seconds)를 키로 사용하여 정확한 중복 제거 및 정렬
3. **3-pass 분할 스크롤** → 가상 스크롤 빈틈 없이 전체 수집
4. **window.__scriptData 저장** → 수집 1회, 읽기 N회로 JS 결과 크기 제한 우회

## 워크플로우

### Phase 1: 사용자 의도 파악

사용자에게 다음을 확인한다:

1. **강의 URL**: 인프런 강의 페이지 URL (없으면 현재 Chrome에 열려있는 탭 확인)
2. **작업 범위**: 전체 강의(모든 챕터) vs 특정 챕터만
3. **출력 폴더**: 파일을 저장할 위치 (기본값: 작업 폴더)

### Phase 2: Chrome 연결 및 커리큘럼 사전 스캔

#### Step 1: Chrome 탭 확인

```
tabs_context_mcp(createIfEmpty: true)
```

연결이 안 되면 사용자에게 Chrome과 Claude in Chrome 확장 프로그램 상태를 확인하도록 안내한다.

#### Step 2: 커리큘럼에서 unitId 목록 수집

강의 대시보드 페이지로 이동하여 모든 강의의 unitId를 미리 수집한다. 이후 강의 간 이동에 unitId 기반 직접 URL 이동을 사용하기 위함이다.

```
navigate(url: "https://www.inflearn.com/course/[강의슬러그]/dashboard", tabId: 탭ID)
```

대시보드에서 커리큘럼의 모든 `a[href*="unitId"]` 링크를 파싱하여 `{순번: unitId, 제목}` 매핑을 생성한다.

> **주의**: 대시보드 접속 시 자동으로 마지막 학습 강의 페이지로 리다이렉트될 수 있다. 이 경우 리다이렉트된 URL에서 courseId를 추출하여 활용한다.

> **주의: 커리큘럼에는 강의(LECTURE) 외에 퀴즈(AI 퀴즈)와 수업 자료 항목도 포함된다.**
> `[data-unit-id]`로 전체 항목을 추출하면 퀴즈와 자료도 섞여 있어 순번이 밀릴 수 있다. 반드시 다음을 확인한다:
> - 강의 제목에 번호(예: "34. 반드시 꼭 알아야 할 것")가 있으면 그 번호를 기준으로 매핑
> - "퀴즈", "AI 퀴즈", "수업 자료", "자료" 텍스트가 포함된 항목은 **강의가 아니므로 제외**
> - `type=LECTURE` 파라미터가 있는 링크만 강의 항목

### Phase 3: 강의 페이지 이동

#### URL 형식 (중요!)

인프런 강의 URL은 다음 형식을 사용한다:

```
https://www.inflearn.com/courses/lecture?courseId=[courseId]&type=LECTURE&unitId=[unitId]&tab=script&subtitleLanguage=ko
```

> **주의**: 과거 형식인 `/course/lecture?courseSlug=...` 는 404를 반환할 수 있다. 반드시 `courses/lecture?courseId=...` 형식을 사용한다.

```
navigate(url: "https://www.inflearn.com/courses/lecture?courseId=[ID]&type=LECTURE&unitId=[unitId]&tab=script&subtitleLanguage=ko", tabId: 탭ID)
```

### Phase 4: 비디오 정지 및 스크립트 전체 로딩 (핵심!)

**반드시 스크립트 수집 전에 실행해야 한다.** 비디오를 일시정지하고 재생 위치를 끝으로 이동시킨다. 이렇게 하면:
- 자동 재생에 의한 스크립트 패널 자동 스크롤이 중단됨
- 강의를 다 본 것과 같은 상태가 되어 모든 스크립트 데이터가 로딩됨

> **⚠ 중요: "자료가 없는 수업이에요" 오탐 방지**
>
> 인프런 페이지에는 **비디오 자막(subtitle) 영역**과 **스크립트 패널(transcript)** 두 가지가 있다. 이 둘은 **완전히 독립적인 기능**이다.
>
> - "자료가 없는 수업이에요" 메시지는 자막 영역(`light-zspjic` 클래스)에 표시될 수 있다
> - **스크립트 패널에는 정상적으로 데이터가 존재**하더라도, 자막 영역에 이 메시지가 뜰 수 있다
> - 따라서 `document.body.innerText.includes('자료가 없는')` 같은 **페이지 전체 텍스트 검사로 스크립트 유무를 판단하면 안 된다**
> - **스크립트 유무 판별은 반드시 스크립트 패널 내 타임스탬프(`^\d+:\d{2}$`) 존재 여부로 해야 한다**

```javascript
(async () => {
  await new Promise(r => setTimeout(r, 3000));
  const video = document.querySelector('video');
  if (video) {
    video.pause();
    video.currentTime = video.duration - 0.1;
    await new Promise(r => setTimeout(r, 2000));
    video.pause();
  }
  const tabs = [...document.querySelectorAll('button, [role="tab"]')];
  const scriptTab = tabs.find(t => t.innerText.trim() === '스크립트');
  if (scriptTab) scriptTab.click();
  await new Promise(r => setTimeout(r, 1500));
  return JSON.stringify({
    paused: video ? video.paused : 'no video',
    currentTime: video ? Math.round(video.currentTime) : 0,
    duration: video ? Math.round(video.duration) : 0
  });
})();
```

결과에서 `paused: true`이고 `currentTime ≈ duration`인지 확인한다. `'no video'`이면 영상이 없는 강의(PDF 등)일 수 있다.

### Phase 5: 스크립트 수집 (Timestamp Map + 3-pass + window 저장)

이것이 이 스킬의 핵심이다. **1회의 JS 호출로 수집 + window 저장**을 동시에 수행하고, 이후 슬라이스 읽기로 전체 데이터를 가져온다.

#### Step 1: 패널 탐색 + 3-pass 수집 + window 저장

```javascript
(async () => {
  // 패널 탐색 (주 셀렉터 → 폴백)
  // ⚠ 패널 판별 기준: 반드시 타임스탬프 정규식(^\d+:\d{2}$)으로 검증해야 한다
  // 비디오 플레이어 UI의 "10:57 / 10:57", "0s" 같은 텍스트를 오탐하지 않도록 주의
  // 첫 번째 스크롤 패널이 비디오 영역일 수 있으므로, 타임스탬프가 있는 패널을 선택해야 한다
  const tsPattern = /^\d+:\d{2}$/m;
  let panel = document.querySelector('[class*="List"][class*="light"]');
  if (panel && !tsPattern.test(panel.innerText)) panel = null;
  if (!panel) {
    for (const d of [...document.querySelectorAll('div')]) {
      const s = getComputedStyle(d);
      if ((s.overflowY==='auto'||s.overflowY==='scroll') && d.scrollHeight > 200 && tsPattern.test(d.innerText)) {
        panel = d; break;
      }
    }
  }
  if (!panel) return JSON.stringify({error: 'no panel', note: 'no scrollable div with timestamp pattern found'});

  // Timestamp Map 수집 (초 단위 키로 정확한 중복 제거)
  let entries = new Map();
  const collect = () => {
    const lines = panel.innerText.split('\n').filter(l => l.trim());
    for (let i = 0; i < lines.length - 1; i++) {
      const m = lines[i].match(/^(\d+):(\d{2})$/);
      if (m && lines[i+1] && !lines[i+1].match(/^\d+:\d{2}$/)) {
        const s = parseInt(m[1]) * 60 + parseInt(m[2]);
        if (!entries.has(s)) entries.set(s, {ts: lines[i], text: lines[i+1]});
      }
    }
  };

  const total = panel.scrollHeight;

  // 3-pass 분할 수집 (0-40%, 30-70%, 60-100%)
  panel.scrollTop = 0; await new Promise(r => setTimeout(r, 500)); collect();
  for (let pos = 0; pos <= total * 0.4; pos += 30) {
    panel.scrollTop = pos; await new Promise(r => setTimeout(r, 100)); collect();
  }
  for (let pos = total * 0.3; pos <= total * 0.7; pos += 30) {
    panel.scrollTop = pos; await new Promise(r => setTimeout(r, 100)); collect();
  }
  for (let pos = total * 0.6; pos <= total; pos += 30) {
    panel.scrollTop = pos; await new Promise(r => setTimeout(r, 100)); collect();
  }

  // 정렬 후 window에 저장 (이후 슬라이스 읽기용)
  const sorted = [...entries.entries()].sort((a, b) => a[0] - b[0]);
  window.__scriptData = sorted.map(([s, e]) => e.ts + '\n' + e.text);

  // 메타 정보 + 첫 번째 청크 반환
  const CHUNK = 40;
  return JSON.stringify({
    total: sorted.length,
    firstTs: sorted[0]?.[1].ts,
    lastTs: sorted[sorted.length - 1]?.[1].ts,
    chunks: Math.ceil(sorted.length / CHUNK),
    chunk0: window.__scriptData.slice(0, CHUNK).join('\n')
  });
})();
```

#### Step 2: 나머지 청크 읽기 (스크롤 없음!)

수집은 이미 완료되었으므로, `window.__scriptData`에서 슬라이스만 꺼낸다. 스크롤을 다시 하지 않는다.

```javascript
// 청크 N 읽기 (N = 1, 2, 3, ...)
const CHUNK = 40;
const start = N * CHUNK;
const data = window.__scriptData.slice(start, start + CHUNK);
JSON.stringify({
  chunk: N,
  hasMore: start + CHUNK < window.__scriptData.length,
  data: data.join('\n')
});
```

`hasMore`가 `false`가 될 때까지 N을 증가시키며 반복한다.

#### 수집 결과 검증

- `firstTs`가 `"0:00"`인지 확인
- `lastTs`가 영상 길이에 근접한지 확인
- `total` 엔트리 수가 영상 길이(분) × 15~25 범위인지 대략 확인

### Phase 6: 다음 챕터 이동

**unitId 기반 직접 URL 이동**을 사용한다. Phase 2에서 수집한 unitId 매핑을 활용한다.

```
navigate(url: "https://www.inflearn.com/courses/lecture?courseId=[ID]&type=LECTURE&unitId=[다음unitId]&tab=script&subtitleLanguage=ko", tabId: 탭ID)
```

> **"다음 수업으로 이동" 버튼 클릭 방식은 사용하지 않는다.** 버튼이 없거나 동작하지 않는 경우가 있고, unitId 직접 이동이 더 안정적이다.

이동 후 Phase 4 → Phase 5를 반복한다.

### Phase 7: MD 파일 생성

수집된 스크립트를 기반으로 두 개의 MD 파일을 생성한다.

#### 파일명 규칙

```
NN_강의제목_script.md
NN_강의제목_notes.md
```

- `NN`: 두 자리 순번 (01, 02, 03...)
- 강의제목: 공백은 언더스코어로 대체, 특수문자 제거

#### 1) script.md — 원본 스크립트

수집된 스크립트를 타임스탬프와 함께 그대로 기록한다:

```markdown
# [강의 제목]

**강의**: [전체 강의명]  
**섹션**: [섹션명]  
**강사**: [강사명]  
**영상 길이**: [영상 길이]  
**수집일**: [날짜]

---

0:00
웹 서비스에서 웹 서버가 하는 역할이 전송입니다.
0:06
mp4 file 형태로 되어 있어서 이걸 그냥 전송을 잘 해주면...

...
```

#### 2) notes.md — 내용 정리

요약이 아니라 **강의 내용을 빠짐없이 구조화**하는 것이 목표다.
이 파일은 두 가지 용도로 활용된다:
- **LLM 학습 데이터**: RAG, 파인튜닝 등 LLM 학습용 고품질 텍스트
- **스터디 참고 자료**: 사람이 읽고 학습할 수 있는 정리된 문서

따라서 시간 표시 없이 순수 내용만 담고, 완전한 문어체로 작성한다.

형식:

```markdown
# [강의 제목]

**강의**: [전체 강의명]  
**섹션**: [섹션명]  
**강사**: [강사명]  
**영상 길이**: [영상 길이]  
**정리일**: [날짜]

---

## 핵심 요약

2~3문장으로 강의의 핵심 메시지를 요약한다.

---

## 주요 내용

### [핵심 주제 소제목 1]

강의 내용을 완전한 문어체 서술문으로 정리한다.

### [핵심 주제 소제목 2]

...

---

## 핵심 키워드

`키워드1`, `키워드2`, `키워드3`
```

내용 정리 시 주의사항:
- **요약하지 말 것**: 강의 내용을 축약하지 않고 구조화만 한다
- **시간 표시 제거**: 타임스탬프나 시간대를 소제목이나 본문에 넣지 않는다
- **완전한 문어체**: "~거든요", "~잖아요" 등 구어체를 "~이다", "~한다" 체의 서술문으로 변환
- **핵심 용어 강조**: 기술 용어나 중요 개념은 **볼드** 처리
- **예시 보존**: 강사가 든 예시, 비유, 사례는 반드시 포함
- **LLM 학습 품질**: 문장이 독립적으로 의미를 가지도록 작성하고, 지시대명사("이것", "그것")보다 구체적 명사를 사용

### Phase 8: 완료 및 전달

모든 파일 생성이 끝나면:

1. 생성된 파일 목록을 사용자에게 보여준다
2. `computer://` 링크로 파일에 접근할 수 있게 한다
3. 전체 강의를 처리한 경우, 목차(index) 역할의 `README.md`도 함께 생성한다

README.md 형식:

```markdown
# [전체 강의명] - 스크립트 & 노트

수집일: [날짜]

| # | 챕터 | 길이 | 파일 |
|---|-------|------|------|
| 01 | 부하분산 기술 | 9:06 | [script](01_부하분산기술_script.md) / [notes](01_부하분산기술_notes.md) |
| 02 | 망사용료 이슈 | 8:45 | [script](02_망사용료이슈_script.md) / [notes](02_망사용료이슈_notes.md) |
| ... | ... | ... | ... |
```

## 에러 처리

| 상황 | 대응 |
|------|------|
| Chrome 확장 미연결 | 사용자에게 Chrome과 확장 프로그램 상태 확인 안내 |
| 스크립트 탭 비어있음 | 스크립트 패널 내 타임스탬프 패턴(`^\d+:\d{2}$`) 부재로 판별. **주의: "자료가 없는 수업이에요" 메시지는 자막(subtitle) 영역에 표시되는 것이며 스크립트 패널 유무와 무관. `document.body.innerText`로 전체 페이지를 검사하면 오탐 발생.** 스크립트 없음 확인 시 다음 강의로 이동 |
| 로그인 필요 | 사용자에게 인프런 로그인 요청 |
| 404 발생 | URL 형식 확인 — `courses/lecture?courseId=...` 형식 사용 여부 점검 |
| `no video` 반환 | 페이지 로딩 대기 후 재시도, 3회 실패 시 스크립트 없는 강의로 판단 |
| `no panel` 반환 | 스크립트 탭 클릭 재시도. 타임스탬프 패턴(`^\d+:\d{2}$`)이 있는 스크롤 패널 탐색. 3회 실패 시 스크립트 없는 강의로 판단 |
| `window.__scriptData` 미존재 | Phase 5 Step 1 재실행 |
| `firstTs`가 `"0:00"`이 아님 | Phase 5 재실행 (수집 누락 가능성) |
