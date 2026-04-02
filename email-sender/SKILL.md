---
name: email-sender
description: "PC의 파일을 탐색하거나 문서/코드/콘텐츠를 생성한 뒤, 결과를 정리하여 사용자의 회사 메일로 Gmail 초안을 만들어주는 스킬. 사용자가 '메일로 보내줘', '이메일로 정리해서 보내', '메일 작성해줘', '파일 찾아서 보내줘', '코드 정리해서 메일로', '보고서 만들어서 메일로', '내 메일로 보내', '이메일 초안', 'email로 보내줘' 등을 언급하면 반드시 이 스킬을 사용한다. 파일 탐색, 문서 생성, 내용 요약 후 메일 발송이 필요한 모든 상황에서 트리거한다."
---

# Email Sender

PC에서 파일을 탐색하거나, 문서/코드/콘텐츠를 생성 및 정리한 뒤, 그 결과를 사용자의 회사 메일로 Gmail 초안을 생성해주는 스킬이다.

## 수신자 결정

수신자는 다음 우선순위로 결정한다:

1. **프롬프트 지정**: 사용자가 "XX@XX.com으로 보내줘"처럼 메일 주소를 직접 지정한 경우 해당 주소를 사용한다.
2. **기본값**: 수신자를 지정하지 않은 경우, 사용자에게 수신자 이메일 주소를 확인한다.

사용자가 수신자를 지정했는지 판단하는 기준: 프롬프트에 이메일 주소 형태(xxx@xxx.xxx)가 포함되어 있으면 해당 주소를 수신자로 사용한다.

## 워크플로우

사용자의 요청을 분석하여 아래 단계를 순서대로 수행한다.

### 1단계: 요청 분석

사용자의 요청을 파악하여 어떤 작업이 필요한지 분류한다:

- **파일 탐색**: 특정 파일이나 내용을 PC에서 찾아야 하는 경우
- **콘텐츠 생성**: 새로운 문서, 코드, 보고서 등을 만들어야 하는 경우
- **내용 정리**: 기존 파일이나 정보를 요약/정리해야 하는 경우
- **복합 작업**: 위 작업들의 조합

### 2단계: 작업 수행

요청 유형에 따라 적절한 도구를 사용한다:

**파일 탐색 시:**
- `Glob`으로 파일명 패턴 검색 (예: `**/*.py`, `**/report*`)
- `Grep`으로 파일 내용 검색
- `Read`로 파일 내용 읽기
- 사용자가 경로를 모를 경우 홈 디렉토리(`~`)부터 탐색 범위를 좁혀간다

**콘텐츠 생성 시:**
- 요청에 맞는 문서, 코드, 보고서 등을 작성한다
- 필요하면 파일로 저장한 뒤 메일 본문에도 포함한다

**내용 정리 시:**
- 탐색한 파일들의 핵심 내용을 추출한다
- 구조화된 형태로 요약 정리한다

### 3단계: 이메일 초안 생성

정리된 내용을 HTML 형식의 이메일 초안으로 만든다.

**이메일 구성 규칙:**

1. **제목**: 내용을 한 줄로 요약한 명확한 제목 (예: "[정리] 프로젝트 X 코드 리뷰 결과")
2. **본문**: `text/html` 형식으로 작성
3. **수신자**: 위 "수신자 결정" 규칙에 따라 결정된 주소 사용

**HTML 본문 템플릿:**

```html
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body { font-family: 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif; line-height: 1.6; color: #333; max-width: 700px; margin: 0 auto; padding: 20px; }
  h1 { color: #1a73e8; border-bottom: 2px solid #1a73e8; padding-bottom: 8px; font-size: 20px; }
  h2 { color: #185abc; font-size: 16px; margin-top: 24px; }
  .section { background: #f8f9fa; border-left: 4px solid #1a73e8; padding: 12px 16px; margin: 12px 0; border-radius: 0 4px 4px 0; }
  .code-block { background: #1e1e1e; color: #d4d4d4; padding: 12px 16px; border-radius: 6px; font-family: 'SF Mono', 'Fira Code', monospace; font-size: 13px; overflow-x: auto; white-space: pre-wrap; }
  table { border-collapse: collapse; width: 100%; margin: 12px 0; }
  th { background: #1a73e8; color: white; padding: 8px 12px; text-align: left; }
  td { border: 1px solid #e0e0e0; padding: 8px 12px; }
  tr:nth-child(even) { background: #f8f9fa; }
  .footer { margin-top: 32px; padding-top: 16px; border-top: 1px solid #e0e0e0; color: #666; font-size: 12px; }
  .highlight { background: #fff3cd; padding: 2px 6px; border-radius: 3px; }
  ul, ol { padding-left: 20px; }
  li { margin: 4px 0; }
</style>
</head>
<body>
  <!-- 여기에 본문 내용 -->

  <div class="footer">
    이 메일은 Claude Code Email Sender 스킬로 자동 생성되었습니다.
  </div>
</body>
</html>
```

**본문 작성 가이드라인:**

- 내용이 길면 `<h2>`로 섹션을 나눈다
- 코드가 포함되면 `.code-block` 클래스를 사용한다
- 핵심 정보는 `.section` 클래스로 강조한다
- 데이터가 표 형태면 `<table>`을 활용한다
- 파일 목록이나 요약 항목은 `<ul>` 또는 `<ol>`을 사용한다

### 4단계: 초안 생성 및 안내

`gmail_create_draft` 도구를 호출하여 초안을 생성한다:

```
to: 수신자 결정 규칙에 따른 이메일 주소
subject: 내용에 맞는 제목
body: 위 템플릿에 맞춘 HTML 본문
contentType: text/html
```

초안 생성 후 사용자에게 알린다:
- 초안이 생성되었음을 알려준다
- 제목과 주요 내용을 간략히 요약한다
- Gmail에서 초안을 확인하고 발송할 수 있다고 안내한다

## 주의사항

- 민감한 정보(비밀번호, API 키 등)가 포함된 파일은 메일 본문에 넣지 않는다. 발견 시 사용자에게 경고한다.
- 파일 내용이 너무 길면 핵심만 요약하고, 전체 내용이 필요하면 별도 파일로 저장 후 경로를 안내한다.
- HTML이 Gmail에서 깨지지 않도록 인라인 스타일 위주로 작성하되, `<style>` 태그도 함께 포함한다.
