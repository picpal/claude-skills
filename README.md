# claude-skills

Claude Code에서 사용하는 커스텀 스킬 모음.

## 사용법

### 심볼릭 링크 방식 (권장)

워크스페이스에서 직접 스킬을 수정하면서 사용하려면 `~/.claude/skills/<name>`을 심볼릭 링크로 연결한다.
`SKILL.md`의 `description` 필드는 single-line 문자열이어야 Skill 도구에서 인식한다.

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
| [dev-harness](./dev-harness) | Classify→Brainstorm→Plan→Execute→QA→Lesson 6단계 코드 작업 파이프라인, `lessons.md` 자동 재투입 | "하네스 돌려줘", "파이프라인으로 진행", "dev harness로" |
| [discord-project-setup](./discord-project-setup) | 프로젝트별 Discord 봇 토큰 연결·상태 확인·제거 (`.discord-token`, `.gitignore`, claude wrapper) | "디스코드 프로젝트 설정", "봇 토큰 연결", "discord setup" |
| [inflearn-script-collector](./inflearn-script-collector) | Claude in Chrome으로 인프런 강의 스크립트를 자동 수집해 챕터별 원본·정리 MD 생성 | "인프런 강의 정리해줘", "강의 스크립트 뽑아줘", "인프런 자막 추출" |
| [resume-checker](./resume-checker) | 한국어 이력서를 인터뷰→분석→AS-IS/TO-BE 첨삭→최종본까지 생성 | "이력서 봐줘", "이력서 첨삭해줘", "자소서 검토" |

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
├── <future-skill>/
│   ├── SKILL.md
│   └── references/     (선택)
└── ...
```

각 스킬은 독립 폴더로 관리되며, 최소 `SKILL.md` 파일 하나로 구성된다.
필요에 따라 `references/`, `scripts/`, `evals/`, `assets/` 하위 폴더를 포함할 수 있다.

## 기여

새 스킬을 추가하려면:

1. 스킬 이름으로 폴더 생성 (kebab-case)
2. `SKILL.md` 작성 — YAML frontmatter에 `name`, `description` 필수, `description`은 single-line
3. 이 README의 스킬 목록 테이블에 추가
