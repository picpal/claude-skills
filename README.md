# cc-skills

Claude Code에서 사용하는 커스텀 스킬 모음.

## 사용법

### 전체 설치

```bash
git clone https://github.com/picpal/cc-skills.git ~/.claude/skills
```

### 개별 스킬만 설치

```bash
# 원하는 스킬 폴더만 복사
git clone https://github.com/picpal/cc-skills.git /tmp/cc-skills
cp -r /tmp/cc-skills/terminal-dev-setup ~/.claude/skills/
```

### 이미 skills 폴더가 있는 경우

```bash
git clone https://github.com/picpal/cc-skills.git /tmp/cc-skills
cp -r /tmp/cc-skills/<skill-name> ~/.claude/skills/
```

## 스킬 목록

| 스킬 | 설명 | 트리거 예시 |
|------|------|------------|
| [terminal-dev-setup](./terminal-dev-setup) | Ghostty, tmux 터미널 개발환경 설정 | "터미널 설정해줘", "ghostty 테마 바꿔줘", "tmux 세팅" |

## 디렉토리 구조

```
cc-skills/
├── README.md
├── terminal-dev-setup/
│   └── SKILL.md
├── <future-skill>/
│   ├── SKILL.md
│   └── references/     (선택)
└── ...
```

각 스킬은 독립 폴더로 관리되며, 최소 `SKILL.md` 파일 하나로 구성된다.
필요에 따라 `references/`, `scripts/`, `assets/` 하위 폴더를 포함할 수 있다.

## 기여

새 스킬을 추가하려면:

1. 스킬 이름으로 폴더 생성 (kebab-case)
2. `SKILL.md` 작성 (YAML frontmatter에 name, description 필수)
3. 이 README의 스킬 목록 테이블에 추가
