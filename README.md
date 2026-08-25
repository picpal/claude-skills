# claude-skills

Claude Code에서 사용하는 커스텀 스킬 모음.

## 사용법

### 심볼릭 링크 방식 (권장)

워크스페이스에서 직접 스킬을 수정하면서 사용하려면 `~/.claude/skills/<name>`을 심볼릭 링크로 연결한다.
`SKILL.md`의 `description`은 유효한 YAML 스칼라면 인식된다. 한 줄 문자열뿐 아니라
블록 스칼라(`|`, `>-`)도 정상 동작한다 — 이 레포의 13개 스킬 중 5개가 블록 스칼라를 쓰고 있다.
다만 블록 인디케이터 없이 줄만 바꿔 이어 쓰면 YAML 파싱이 깨지므로, 여러 줄이 필요하면 `|` 또는 `>-`를 반드시 붙인다.

```bash
git clone https://github.com/picpal/claude-skills.git ~/workspace/claude-skills
ln -s ~/workspace/claude-skills/<skill-name> ~/.claude/skills/<skill-name>
```

### 전체 설치 (복사 방식)

```bash
git clone https://github.com/picpal/claude-skills.git ~/.claude/skills
```

### 개별 스킬만 설치 (복사 방식)

```bash
git clone https://github.com/picpal/claude-skills.git /tmp/claude-skills
cp -r /tmp/claude-skills/<skill-name> ~/.claude/skills/
```

## 스킬 목록

| 스킬 | 설명 | 트리거 예시 |
|------|------|------------|
| [terminal-dev-setup](./terminal-dev-setup) | Ghostty, tmux 터미널 개발환경 설정 | "터미널 설정해줘", "ghostty 테마 바꿔줘", "tmux 세팅" |
| [tmux-work-setting](./tmux-work-setting) | tmux 세션/윈도우/pane을 구성하고 각 pane에서 Claude Code를 자동 실행 | "tmux 작업환경 세팅", "클로드 여러 개 띄워줘", "멀티 pane 세션 만들어줘" |
| [email-sender](./email-sender) | 파일 탐색·문서 생성 결과를 정리해 Gmail 초안으로 작성 | "메일로 보내줘", "파일 찾아서 메일로", "보고서 만들어서 이메일로" |
| [evidence-capture](./evidence-capture) | 소스코드·웹·터미널·로그를 PNG 스크린샷으로 캡처해 증적 폴더에 저장 | "증적 캡처해줘", "스크린샷 찍어줘", "감사 자료 수집" |
| [dev-harness](./dev-harness) | Classify→Brainstorm→Plan→Execute→QA→Review→Lesson 7단계 코드 작업 파이프라인. maker(Execute)와 컨텍스트 격리된 fresh-eyes checker(Review) 분리, `lessons.md` 자동 재투입 | "하네스 돌려줘", "파이프라인으로 진행", "dev harness로" |
| [discord-project-setup](./discord-project-setup) | 프로젝트별 Discord 봇 토큰 연결·상태 확인·제거 (`.discord-token`, `.gitignore`, claude wrapper) | "디스코드 프로젝트 설정", "봇 토큰 연결", "discord setup" |
| [inflearn-script-collector](./inflearn-script-collector) | Claude in Chrome으로 인프런 강의 스크립트를 자동 수집해 챕터별 원본·정리 MD 생성 | "인프런 강의 정리해줘", "강의 스크립트 뽑아줘", "인프런 자막 추출" |
| [resume-checker](./resume-checker) | 한국어 이력서를 인터뷰→분석→AS-IS/TO-BE 첨삭→최종본까지 생성 | "이력서 봐줘", "이력서 첨삭해줘", "자소서 검토" |
| [gen-report-monodeck](./gen-report-monodeck) | 구조화된 보고서를 흑백 에디토리얼 "덱" 스타일 스크롤 HTML로 렌더링 | "보고서 html", "리포트 만들어줘", "모노크롬 보고서" |
| [gen-report-monodeck-ppt](./gen-report-monodeck-ppt) | gen-report-monodeck과 동일한 모노크롬 테마를 유지하되, 스크롤 대신 화살표 키·버튼·스와이프로 한 장씩 넘기는 PPT 형태 슬라이드 HTML로 렌더링 | "ppt 형태 html", "슬라이드로 넘기는 html", "발표자료 html", "피치덱 만들어줘" |
| [spotify-to-ytmusic](./spotify-to-ytmusic) | 공유받은 Spotify 플레이리스트를 YouTube Music에 동일 구성으로 복제. embed 파싱이라 Spotify 인증·Premium 불필요, 재실행 시 새 곡만 증분 동기화 | "스포티파이 플레이리스트 유튜브뮤직으로", "플레이리스트 옮겨줘", "플레이리스트 복제" |
| [authoring-e2e-suites](./authoring-e2e-suites) | 화면별 Playwright E2E 스위트를 "실행만 하면 재검증되는" 회귀 자산으로 작성. 하네스(프로덕션 빌드 서빙·상태 리셋·storageState 인증·포트 스코프 격리) 확정 후 파일럿 → 화면군 → 전체 합주 3단 그린 게이트 | "E2E 테스트 만들어줘", "화면 테스트 자동화", "단독은 통과하는데 합주에서 401 터져" |
| [youtube-study-notes](./youtube-study-notes) | YouTube 자막을 Chrome 쿠키 인증으로 추출(멤버십·로그인 영상 포함), 라이브 누적 자막 중복을 정제해 원본 .txt + 학습노트 .md 생성 | "유튜브 강의 정리해줘", "자막 추출", "멤버십 영상 학습 노트" |
| [vision](./vision) | 39종 에디토리얼 다이어그램(아키텍처·시퀀스·스윔레인·Sankey·Wardley 등)을 self-contained HTML/SVG로 생성. `cathrynlavery/diagram-design` v2.6 포크 — deep-teal 스킨 + Pretendard로 한글 라벨 지원, 52종 예시를 담은 모노톤 컨택트시트 갤러리("갤러리 보여줘"로 호출), §6 커넥터 규칙·간격·렌더링된 텍스트 폭 검사기 자체 탑재 | "다이어그램 만들어줘", "아키텍처 도식화", "플로우차트 그려줘" |

## 디렉토리 구조

```
claude-skills/
├── README.md
├── terminal-dev-setup/
│   └── SKILL.md
├── tmux-work-setting/
│   └── SKILL.md
├── email-sender/
│   └── SKILL.md
├── evidence-capture/
│   ├── SKILL.md
│   └── scripts/
├── dev-harness/
│   ├── SKILL.md
│   ├── config.yaml
│   └── references/
├── discord-project-setup/
│   ├── SKILL.md
│   ├── scripts/
│   └── evals/
├── inflearn-script-collector/
│   └── SKILL.md
├── resume-checker/
│   ├── SKILL.md
│   └── references/
├── gen-report-monodeck/
│   ├── SKILL.md
│   └── assets/
├── gen-report-monodeck-ppt/
│   ├── SKILL.md
│   └── assets/
├── spotify-to-ytmusic/
│   ├── SKILL.md
│   ├── requirements.txt
│   └── scripts/
├── authoring-e2e-suites/
│   ├── SKILL.md
│   ├── references/
│   ├── templates/
│   └── evals/
├── youtube-study-notes/
│   ├── SKILL.md
│   └── scripts/
├── docs/               (스킬 설계 스펙 · 구현 계획)
│   └── superpowers/
├── workspace/          (타 에이전트 포팅 산출물)
│   └── codex-skills/
├── <future-skill>/
│   ├── SKILL.md
│   └── references/     (선택)
├── vision/
│   ├── SKILL.md
│   ├── lessons.md      결함·원인·규칙 기록 (수정 전 필독)
│   ├── LICENSE         원본 MIT
│   ├── NOTICE          포크 출처·변경내역·제약
│   ├── references/     39종 type-*.md + style-guide.md
│   ├── assets/         예시 181개 (EN 142 + KO 39) + index.html 갤러리
│   ├── scripts/        self_check.py
│   └── tools/          lint-skin · verify-geometry · verify-connectors ·
│                       verify-spacing · verify-text · svgstyle · build-gallery
└── ...
```

각 스킬은 독립 폴더로 관리되며, 최소 `SKILL.md` 파일 하나로 구성된다.
필요에 따라 `references/`, `scripts/`, `evals/`, `assets/` 하위 폴더를 포함할 수 있다.

## 기여

새 스킬을 추가하려면:

1. 스킬 이름으로 폴더 생성 (kebab-case)
2. `SKILL.md` 작성 — YAML frontmatter에 `name`, `description` 필수.
   `description`은 한 줄 문자열 또는 블록 스칼라(`|`, `>-`) 중 하나로 쓴다 (인디케이터 없는 줄바꿈은 파싱 실패)
3. 이 README의 스킬 목록 테이블에 추가
