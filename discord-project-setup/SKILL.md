---
name: discord-project-setup
description: "프로젝트별 Discord 봇 연결 설정 스킬. .discord-token 생성, .gitignore 추가, 셸 wrapper 확인을 한번에 처리한다. 사용자가 '디스코드 프로젝트 설정', '봇 토큰 연결', 'discord setup', 'discord project setup', '프로젝트 디스코드 연결', '봇 세팅', 'discord token', '디스코드 토큰', '디스코드 봇 설정', '새 프로젝트 디스코드 연결해줘', 'discord bot connect' 등을 언급하면 이 스킬을 사용한다. 프로젝트 디렉토리에서 Discord 봇을 연결하거나, 토큰 상태를 확인하거나, 기존 토큰을 제거하는 모든 상황에 해당한다."
---

# Discord Project Setup

프로젝트별로 Discord 봇을 분리 연결하기 위한 설정 스킬.
각 프로젝트 디렉토리에 `.discord-token`을 생성하고, `claude` 실행 시
자동으로 해당 토큰이 로드되도록 구성한다.

## 구조

```
~/.zshrc (또는 ~/.bashrc)
  └── claude() wrapper — 실행 시 .discord-token → ~/.claude/channels/discord/.env 복사

프로젝트/
  ├── .discord-token        ← DISCORD_BOT_TOKEN=MTxx... (chmod 600)
  └── .gitignore            ← .discord-token 포함
```

## 번들 스크립트

`scripts/setup.sh`가 토큰 설정·상태 확인·제거의 핵심 작업을 자동화한다.
가능하면 이 스크립트를 직접 실행해서 작업을 처리하고, 스크립트가 `WRAPPER_NEEDED`를
출력한 경우에만 wrapper 추가 과정을 별도로 진행한다.

```bash
# 토큰 설정
bash <skill-path>/scripts/setup.sh <token>

# 상태 확인
bash <skill-path>/scripts/setup.sh status

# 토큰 제거
bash <skill-path>/scripts/setup.sh clear
```

`<skill-path>`는 이 SKILL.md가 위치한 디렉토리 경로로 치환한다.

## 실행 흐름

Arguments: `$ARGUMENTS`

---

### `<token>` 전달 시 — 전체 세팅

`$ARGUMENTS`가 비어있지 않고 `clear`, `status`가 아닌 경우 봇 토큰으로 취급한다.

**스크립트 사용 가능 시:** `bash <skill-path>/scripts/setup.sh <token>` 실행.
스크립트가 토큰 검증, 파일 생성, gitignore 확인, 글로벌 env 적용을 모두 처리한다.
출력에 `WRAPPER_NEEDED`가 포함되면 아래 Step 3으로 이동해 wrapper를 추가한다.

**스크립트 사용 불가 시:** 아래 단계를 수동으로 진행한다.

**Step 1: 토큰 검증 및 `.discord-token` 생성**

먼저 토큰 형식을 확인한다. Discord 봇 토큰은 점(`.`)으로 구분된 3개 파트로
이루어진 base64 문자열이며, 보통 70자 이상이다.

- 50자 미만이면 오류로 처리하고 사용자에게 재확인을 요청한다.
- 점 구분자가 2개가 아니면 경고를 표시하되 계속 진행한다.

검증을 통과하면 현재 작업 디렉토리에 `.discord-token` 파일을 생성한다.

```
DISCORD_BOT_TOKEN=<token>
```

- 파일이 이미 존재하면 `DISCORD_BOT_TOKEN=` 라인만 업데이트하고 나머지는 보존한다.
- `chmod 600 .discord-token` 적용.

**Step 2: `.gitignore` 확인**

현재 디렉토리의 `.gitignore`를 확인한다.

- `.discord-token` 항목이 없으면 맨 아래에 추가.
- 이미 있으면 건너뛴다.
- `.gitignore` 파일이 없으면 새로 생성하고 `.discord-token`을 넣는다.

**Step 3: 셸 wrapper 확인**

사용자의 기본 셸에 맞는 rc 파일을 확인한다.
- zsh → `~/.zshrc`
- bash → `~/.bashrc`
- 기타 → `~/.{셸이름}rc`

rc 파일을 읽어 `claude()` 함수가 `.discord-token`을 복사하는 wrapper로
정의되어 있는지 확인한다.

- wrapper가 있으면 "확인됨"으로 표시.
- wrapper가 없으면 아래 코드를 rc 파일에 추가할지 사용자에게 물어본다:

```bash
# Claude Code with per-project Discord token
unalias claude 2>/dev/null
claude() {
  if [[ -f "$(pwd)/.discord-token" ]]; then
    cp "$(pwd)/.discord-token" ~/.claude/channels/discord/.env
    chmod 600 ~/.claude/channels/discord/.env
  fi
  command claude --dangerously-skip-permissions --channels plugin:discord@claude-plugins-official "$@"
}
```

주의사항:
- 기존 `alias claude=...`가 있으면 제거하고 wrapper 함수로 교체한다.
- 기존 wrapper가 이미 있으면 수정하지 않고 "확인됨"으로만 표시한다.
- bash 사용자의 경우 `[[ ]]` 구문이 작동하는지 확인한다 (bash 4+ 필수는 아니지만 권장).

**Step 4: 글로벌 `.env` 즉시 적용**

`.discord-token`을 `~/.claude/channels/discord/.env`에 복사한다.
`mkdir -p ~/.claude/channels/discord` 선행 실행.

**Step 5: 결과 출력**

```
.discord-token 생성 완료 (chmod 600)
.gitignore에 .discord-token 추가됨
~/.zshrc wrapper 확인됨        ← 또는 ~/.bashrc 등 실제 파일명
글로벌 .env 즉시 적용됨

다음 단계: 이 세션을 종료하고 `claude`를 다시 실행하면
Discord 봇이 자동 연결됩니다.
```

---

### No args 또는 `status` — 상태 확인

**스크립트 사용 가능 시:** `bash <skill-path>/scripts/setup.sh status` 실행.

**스크립트 사용 불가 시:** 아래 단계를 수동으로 진행한다.

1. 현재 디렉토리에 `.discord-token`이 있는지 확인.
   - 있으면: 토큰 앞 6자 + `...MASKED` 형태로 표시.
   - 없으면: "설정 안 됨" 표시.

2. `.gitignore`에 `.discord-token`이 포함되어 있는지 확인.

3. 셸 rc 파일(사용자 기본 셸 기준)에 wrapper가 있는지 확인.

4. 글로벌 `~/.claude/channels/discord/.env`와 현재 `.discord-token`의
   토큰이 일치하는지 확인.

5. 상태 요약 출력:

```
[프로젝트]  <현재 디렉토리 basename>
[토큰]     MTxx12...MASKED (설정됨 / 설정 안 됨)
[gitignore] 포함됨 / 미포함
[wrapper]  확인됨 / 미설정    (zshrc / bashrc)
[글로벌]   일치 / 불일치 / 미적용
```

---

### `clear` — 제거

**스크립트 사용 가능 시:** `bash <skill-path>/scripts/setup.sh clear` 실행.

**스크립트 사용 불가 시:** 아래 단계를 수동으로 진행한다.

1. 현재 디렉토리의 `.discord-token` 삭제.
2. `.gitignore`에서 `.discord-token` 항목 제거.
3. 글로벌 `.env`는 건드리지 않는다 (다른 프로젝트 것일 수 있음).
4. 확인 메시지 출력.

---

## 에러 처리

이 스킬은 보안이 관련된 파일을 다루므로, 에러 상황을 명확히 처리해야 한다.

| 상황 | 대응 |
|------|------|
| 토큰이 50자 미만 | 오류 출력, 설정 중단, 사용자에게 재확인 요청 |
| `.discord-token` 쓰기 권한 없음 | 디렉토리 권한 확인 안내, `sudo` 사용 지양 |
| `.gitignore` 수정 실패 | 수동 추가 방법 안내 |
| `~/.claude/channels/discord/` 생성 실패 | 홈 디렉토리 경로 및 권한 확인 |
| rc 파일이 존재하지 않음 | 새로 생성할지 사용자에게 확인 |
| 이미 다른 프로젝트의 글로벌 토큰이 적용됨 | 덮어쓴다는 점을 명시하고 진행 |

## 보안 주의사항

- 토큰은 절대 출력에 전체를 표시하지 않는다. 항상 앞 6자 + `...MASKED`.
- `.discord-token`은 반드시 `chmod 600` 적용.
- `.gitignore`에 반드시 포함되어야 한다. 누락 시 경고 출력.
- `.discord-token`을 git에 커밋하지 않도록 주의를 안내한다.
- 토큰 값을 채팅 출력이나 로그에 그대로 노출하지 않는다.
