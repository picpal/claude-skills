---
name: tmux-work-setting
description: "tmux 세션을 생성하고 윈도우/pane을 구성하여 각 pane에서 Claude Code를 실행하는 스킬. 사용자가 tmux 작업환경 세팅, 멀티 클로드 실행, tmux work setting, 작업 세션 만들기, tmux 세션 구성, 멀티 pane 클로드, 여러 프로젝트 동시 실행, tmux 클로드 세팅 등을 언급하면 이 스킬을 사용한다. 'tmux 세팅해줘', '작업환경 구성', 'claude 여러개 띄워줘' 같은 요청에도 트리거한다."
---

# tmux Work Setting

tmux 세션을 생성하고, 윈도우별로 pane을 분할한 뒤 각 pane에서 Claude Code를 프로젝트 디렉토리 기반으로 실행한다.

## 실행 흐름

전체 과정을 AskUserQuestion을 통해 대화형으로 진행한다. 각 단계에서 사용자 입력을 받고, 모든 tmux 명령은 Agent(bypassPermissions)를 통해 실행한다.

### Step 1: 세션명 결정

- 기본 세션명: `work`
- 먼저 `tmux list-sessions`로 기존 세션 확인
- `work` 세션이 이미 존재하면 사용자에게 다른 세션명을 입력받음
- 존재하지 않으면 `work`로 진행

### Step 2: 윈도우 개수 입력

사용자에게 생성할 윈도우 개수를 물어본다 (1~5 범위 권장).

### Step 3: 각 윈도우별 pane 수 입력

각 윈도우마다 pane 수를 입력받는다 (1~4, 최대 4개).

### Step 4: 프로젝트 디렉토리 매핑

**2단계 접근:**

1. **Base workspace 경로 확인** — 기본값은 현재 작업 디렉토리(`$PWD`). 사용자에게 확인받음.
2. **하위 디렉토리 목록 표시** — base 경로 아래의 디렉토리를 번호 목록으로 보여줌:
   ```
   📂 ~/Desktop/workspace 하위 프로젝트:
     1. claude-code-hub
     2. morning-briefing
     3. my-api-server
   ```
3. **각 pane에 프로젝트 할당** — 윈도우/pane별로 프로젝트를 선택받음:
   - 번호 입력 → 목록에서 선택
   - 절대경로 입력(`/`로 시작) → 그대로 사용
   - 이름 입력 → base path에 연결

형식 예시:
```
윈도우 T-01:
  Pane 1 프로젝트: 1
  Pane 2 프로젝트: 3
윈도우 T-02:
  Pane 1 프로젝트: 2
```

여러 pane을 한 번에 입력받을 수 있도록 쉼표 구분도 지원한다: `1, 3` → Pane 1에 1번, Pane 2에 3번.

### Step 5: tmux 세션 생성 및 구성

Agent(bypassPermissions)를 사용하여 다음 tmux 명령들을 순차 실행한다.

#### 세션 및 윈도우 생성

```bash
# 세션 생성 (첫 번째 윈도우 포함)
tmux new-session -d -s {session_name} -n T-01

# 추가 윈도우 생성
tmux new-window -t {session_name} -n T-02
tmux new-window -t {session_name} -n T-03
```

#### Pane 분할 규칙

pane 수에 따른 분할 방식:

**1 pane** — 분할 없음
```
┌─────────────┐
│   pane 0    │
└─────────────┘
```

**2 panes** — 수직 분할
```
┌──────┬──────┐
│  p0  │  p1  │
└──────┴──────┘
```
```bash
tmux split-window -h -t {session}:{window}
tmux select-layout -t {session}:{window} even-horizontal
```

**3 panes** — 수직 분할 후 첫 번째 pane 수평 분할
```
┌──────┬──────┐
│  p0  │      │
├──────┤  p2  │
│  p1  │      │
└──────┴──────┘
```
```bash
tmux split-window -h -t {session}:{window}
tmux split-window -v -t {session}:{window}.0
tmux select-layout -t {session}:{window} main-vertical
```

**4 panes** — 2x2 격자
```
┌──────┬──────┐
│  p0  │  p2  │
├──────┼──────┤
│  p1  │  p3  │
└──────┴──────┘
```
```bash
tmux split-window -h -t {session}:{window}
tmux split-window -v -t {session}:{window}.0
tmux split-window -v -t {session}:{window}.2
tmux select-layout -t {session}:{window} tiled
```

#### Claude Code 실행

각 pane에서 프로젝트 디렉토리로 이동 후 Claude Code를 실행한다:

```bash
tmux send-keys -t {session}:{window}.{pane} 'cd {project_path} && claude --dangerously-skip-permissions --channels plugin:discord@claude-plugins-official' Enter
```

**pane 실행 순서**: 한 윈도우 내 모든 pane에 send-keys를 보낸 후, 다음 윈도우로 이동한다. 각 send-keys 사이에 1초 간격(`sleep 1`)을 두어 안정적으로 실행되도록 한다.

### Step 6: 에러 처리

각 pane에서 Claude Code 실행 후 2~3초 대기 뒤 `tmux capture-pane`으로 상태를 확인한다.

- 디렉토리가 존재하지 않는 경우 → 1회 재시도 (경로 재확인)
- 재시도 실패 시 → 사용자에게 해당 pane의 문제를 설명하고 다음 중 선택:
  - 다른 디렉토리 지정
  - 해당 pane 건너뛰기
  - 전체 중단

### Step 7: 최종 확인

모든 pane 실행 완료 후, 구성 결과를 요약 출력한다:

```
✅ tmux 세션 '{session_name}' 구성 완료

  T-01: claude-code-hub | morning-briefing
  T-02: my-api-server | frontend-app | backend

tmux attach -t {session_name} 으로 접속하세요.
```

## 주의사항

- 모든 tmux 명령은 반드시 Agent(mode: bypassPermissions)를 통해 실행한다. 직접 Bash로 실행하면 hook에 의해 차단될 수 있다.
- `--dangerously-skip-permissions`는 모든 pane에 기본 적용된다.
- `--channels plugin:discord@claude-plugins-official`는 모든 pane에 기본 적용된다.
- 윈도우 이름은 T-01, T-02, ... 형식으로 순차 증가한다.
- pane 크기는 균등 분할(even layout)을 적용한다.
