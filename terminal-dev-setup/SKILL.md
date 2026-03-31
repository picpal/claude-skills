---
name: terminal-dev-setup
description: "터미널 개발환경 설정 스킬. Ghostty 터미널과 tmux의 설정, 폰트 설치, 테마 적용, 키바인딩, 편의 기능 구성을 도와준다. 사용자가 터미널 설정, 개발환경 설정, Ghostty 설정, tmux 설정, 터미널 폰트, 터미널 테마, 터미널 단축키 등을 언급하면 이 스킬을 사용한다. '터미널 꾸미기', '터미널 세팅', 'ghostty 설정해줘', 'tmux 설정해줘' 같은 요청에도 트리거한다."
---

# Terminal Dev Setup

터미널 개발환경(Ghostty, tmux)의 설정을 도와주는 스킬이다.
사용자의 요청에 따라 설정 적용, 폰트/테마 추천, cheatsheet 생성을 수행한다.

## 작업 흐름

### 1. 요청 파악

사용자의 요청을 아래 카테고리로 분류한다:

- **설치**: 도구가 없으면 Homebrew로 설치
- **설정 변경**: 특정 옵션 추가/수정 (폰트, 테마, 키바인딩 등)
- **환경 구축**: 처음부터 설정 파일 생성
- **추천**: 테마, 폰트, 유용한 설정 추천
- **cheatsheet 생성**: 주요 설정/단축키 정리 문서 작성

### 2. 설치 확인

설정 작업 전에 해당 도구가 설치되어 있는지 확인한다. 미설치 시 Homebrew를 통해 설치한다.

```bash
# Homebrew 설치 여부 확인
which brew

# Ghostty 설치
brew install --cask ghostty

# tmux 설치
brew install tmux

# TPM (tmux Plugin Manager) 설치
git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm
```

Homebrew가 없으면 먼저 Homebrew 설치를 안내한다:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

폰트 설치도 Homebrew로 처리한다:
```bash
brew install --cask font-jetbrains-mono   # JetBrains Mono
brew install --cask d2coding-font          # D2Coding
brew install --cask font-fira-code         # Fira Code
brew install --cask font-hack              # Hack
```

### 3. 기존 설정 백업

설정 파일을 새로 생성하거나 대폭 변경할 때, 기존 파일이 있으면 반드시 백업한다.
사용자에게 백업 여부를 확인한 뒤 진행한다.

```bash
# Ghostty 설정 백업
cp ~/Library/Application\ Support/com.mitchellh.ghostty/config.ghostty \
   ~/Library/Application\ Support/com.mitchellh.ghostty/config.ghostty.bak.$(date +%Y%m%d)

# tmux 설정 백업
cp ~/.tmux.conf ~/.tmux.conf.bak.$(date +%Y%m%d)
```

부분 수정(Edit)의 경우 백업 없이 진행해도 된다. "처음부터 설정해줘" 같은 전체 재작성 요청일 때만 백업한다.

### 4. 현재 상태 확인

설정을 변경하기 전에 반드시 현재 설정 파일을 읽어 기존 설정을 파악한다.

**Ghostty 설정 파일 경로:**
- macOS: `~/Library/Application Support/com.mitchellh.ghostty/config.ghostty`
- Linux: `~/.config/ghostty/config`

**tmux 설정 파일 경로:**
- `~/.tmux.conf`

### 5. 설정 적용

설정을 변경할 때는 기존 파일을 Edit 도구로 수정한다. 전체 덮어쓰기가 아닌 필요한 부분만 수정한다.

---

## Ghostty 설정 가이드

### 설정 파일 형식
`key = value` 형식. 한 줄에 하나의 설정.

### 주요 설정 카테고리

#### Font
| 키 | 설명 | 예시 |
|---|---|---|
| `font-family` | 기본 폰트 | `JetBrains Mono` |
| `font-size` | 폰트 크기 (소수점 가능) | `14` |
| `font-codepoint-map` | 유니코드 범위별 폰트 분리 | `U+AC00-U+D7AF=D2Coding` |
| `font-style` | 폰트 스타일 (false로 비활성화) | `Regular` |
| `font-feature` | OpenType 기능 | `-calt` |

한글 폰트 분리 설정 시 codepoint 범위:
- 한글 자모: `U+1100-U+11FF`
- 호환 자모: `U+3130-U+318F`
- 한글 음절: `U+AC00-U+D7AF`

#### Theme
`ghostty +list-themes`로 사용 가능한 테마 목록 확인.
Light/Dark 자동 전환: `theme = light:테마명,dark:테마명`

**인기 Dark 테마:** Catppuccin Mocha, TokyoNight Storm, Dracula, Rose Pine, Kanagawa Wave, Nord, Gruvbox Dark, Everforest Dark Hard
**인기 Light 테마:** Catppuccin Latte, Rose Pine Dawn, GitHub Light Default, TokyoNight Day

**추천 조합:**
- `light:Catppuccin Latte,dark:Catppuccin Mocha`
- `light:Rose Pine Dawn,dark:Rose Pine Moon`
- `light:GitHub Light Default,dark:TokyoNight Storm`

#### 외관
| 키 | 설명 | 예시 |
|---|---|---|
| `background-opacity` | 배경 투명도 (0.0~1.0) | `0.92` |
| `background-blur` | 투명 배경 블러 | `true` |
| `cursor-style` | 커서 모양 | `bar` / `block` / `underline` |
| `cursor-style-blink` | 커서 깜빡임 | `false` |
| `window-padding-x/y` | 창 내부 여백 | `4` |
| `window-decoration` | 타이틀바 | `none` / `auto` |

#### 편의 기능
| 키 | 설명 | 예시 |
|---|---|---|
| `clipboard-paste-protection` | 줄바꿈 포함 붙여넣기 경고 | `true` |
| `clipboard-trim-trailing-spaces` | 복사 시 줄 끝 공백 제거 | `true` |
| `copy-on-select` | 선택만으로 자동 복사 | `clipboard` |
| `link-url` | URL 자동 감지 | `true` |
| `mouse-hide-while-typing` | 타이핑 중 마우스 숨김 | `true` |
| `mouse-scroll-multiplier` | 스크롤 속도 | `3` |
| `window-save-state` | 창 상태 유지 | `always` |
| `confirm-close-surface` | 닫기 확인 생략 | `false` |
| `notify-on-command-finish` | 명령 완료 알림 | `unfocused` |

#### 키바인딩
문법: `keybind = modifier+key=action`
수식키: `shift`, `ctrl`, `alt`(opt), `super`(cmd)

**유용한 커스텀 키바인딩:**
```
keybind = super+shift+enter=toggle_split_zoom
keybind = super+ctrl+equal=equalize_splits
```

**기본 단축키 (macOS):**
- `Cmd+N` 새 윈도우 / `Cmd+T` 새 탭 / `Cmd+W` 닫기
- `Cmd+D` 오른쪽 분할 / `Cmd+Shift+D` 아래 분할
- `Cmd+[/]` split 이동
- `Cmd+Enter` 전체화면
- `Cmd++/-/0` 폰트 크기 조절
- `Cmd+,` 설정 열기 / `Cmd+Shift+,` 설정 리로드
- `Cmd+F` 검색 / `Cmd+K` 화면 클리어

#### 유용한 CLI 명령
- `ghostty +list-fonts` - 폰트 목록
- `ghostty +list-themes` - 테마 목록
- `ghostty +list-keybinds --default` - 기본 키바인딩
- `ghostty +list-actions` - 사용 가능한 액션
- `ghostty +show-config` - 현재 설정 확인
- `ghostty +validate-config` - 설정 유효성 검사

### 폰트 설치

Homebrew로 설치:
```bash
brew install --cask font-jetbrains-mono
brew install --cask d2coding-font
brew install --cask font-fira-code
brew install --cask font-hack
```

설치 후 `ghostty +list-fonts`로 인식 확인.

---

## tmux 설정 가이드

### 핵심 설정

#### Prefix 키 변경
기본 `Ctrl+b`는 손이 불편하므로 `Ctrl+a`로 변경하는 것이 일반적:
```
unbind C-b
set -g prefix C-a
bind C-a send-prefix
```

#### 필수 기본값
```
set -g mouse on                     # 마우스 지원
setw -g mode-keys vi                 # vi 키바인딩
set -g base-index 1                  # 윈도우 번호 1부터
setw -g pane-base-index 1            # 패인 번호 1부터
set -g renumber-windows on           # 윈도우 번호 자동 재정렬
set -g history-limit 50000           # 스크롤백 버퍼
set -g escape-time 0                 # ESC 지연 제거 (vim 필수)
set -g focus-events on               # 포커스 이벤트 전달
```

#### 터미널 컬러
```
set -g default-terminal "tmux-256color"
set -ga terminal-overrides ",xterm-256color:Tc"
```

#### 직관적 패인 분할
```
bind | split-window -h -c "#{pane_current_path}"
bind - split-window -v -c "#{pane_current_path}"
bind c new-window -c "#{pane_current_path}"
```

#### vim 스타일 패인 이동/리사이즈
```
bind h select-pane -L
bind j select-pane -D
bind k select-pane -U
bind l select-pane -R
bind -r H resize-pane -L 5
bind -r J resize-pane -D 5
bind -r K resize-pane -U 5
bind -r L resize-pane -R 5
```

#### 설정 리로드
```
bind r source-file ~/.tmux.conf \; display "Config reloaded!"
```

#### 동기화 모드 (모든 패인에 동시 입력)
```
bind S setw synchronize-panes \; display "Sync #{?synchronize-panes,ON,OFF}"
```

#### macOS 클립보드 연동
```
bind -T copy-mode-vi v send-keys -X begin-selection
bind -T copy-mode-vi y send-keys -X copy-pipe-and-cancel "pbcopy"
bind -T copy-mode-vi Enter send-keys -X copy-pipe-and-cancel "pbcopy"
```

### 상태바 스타일링

인기 컬러 스킴 예시 (Catppuccin 계열):
```
set -g status-position bottom
set -g status-style bg=#1e1e2e,fg=#cdd6f4
set -g status-left "#[bg=#89b4fa,fg=#1e1e2e,bold]  #S #[default] "
set -g status-right "#[fg=#a6adc8] %Y-%m-%d  %H:%M #[default]"
setw -g window-status-format " #I:#W "
setw -g window-status-current-format "#[bg=#74c7ec,fg=#1e1e2e,bold] #I:#W "
set -g pane-border-style fg=#45475a
set -g pane-active-border-style fg=#89b4fa
```

### 추천 플러그인 (TPM)

| 플러그인 | 기능 |
|---------|------|
| `tmux-resurrect` | 세션 저장/복원 |
| `tmux-continuum` | 자동 저장/복원 |
| `tmux-yank` | 시스템 클립보드 복사 |
| `tmux-sensible` | 합리적 기본값 모음 |

TPM 설치:
```bash
git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm
```

플러그인 설치: `prefix + I` (대문자)

### 주요 단축키 (Prefix = Ctrl+a 기준)

**세션:** `d` 분리 / `s` 세션 목록 / `$` 이름 변경
**윈도우:** `c` 새 윈도우 / `n/p` 다음/이전 / `번호` 이동 / `,` 이름 변경 / `&` 닫기
**패인:** `|` 세로 분할 / `-` 가로 분할 / `h/j/k/l` 이동 / `x` 닫기 / `z` 줌 토글
**기타:** `r` 설정 리로드 / `S` 동기화 토글 / `[` 복사 모드 / `]` 붙여넣기

---

## Cheatsheet 생성

사용자가 cheatsheet를 요청하면 지정된 경로에 마크다운(.md) 파일로 생성한다.

파일명 규칙: `{도구명}-cheatsheet.md` (예: `ghostty-cheatsheet.md`, `tmux-cheatsheet.md`)

cheatsheet에 포함할 내용:
1. 설정 파일 경로
2. 주요 설정 옵션 (표 형식)
3. 단축키 모음 (표 형식)
4. 유용한 명령어
5. 추천 설정 예시

---

## 설정 보고서 생성

설정 작업이 완료되면 사용자가 지정한 경로(또는 cheatsheet와 같은 경로)에 설정 보고서를 마크다운 파일로 생성한다.

파일명 규칙: `{도구명}-setup-report.md` (예: `ghostty-setup-report.md`, `tmux-setup-report.md`)
여러 도구를 함께 설정한 경우: `terminal-setup-report.md`

### 보고서 템플릿

```markdown
# 터미널 개발환경 설정 보고서

- 작성일: YYYY-MM-DD
- 대상 도구: (설정한 도구 목록)

---

## 설치 항목

| 항목 | 설치 방법 | 상태 |
|------|----------|:----:|
| (도구/폰트/플러그인명) | (brew 명령 등) | 신규설치 / 기존설치 |

## 설정 파일

| 도구 | 설정 파일 경로 |
|------|---------------|
| (도구명) | (경로) |

## 적용된 설정 요약

### (도구명)

| 카테고리 | 설정 | 값 | 설명 |
|---------|------|---|------|
| Font | font-family | JetBrains Mono | 영문 폰트 |
| Font | font-codepoint-map | U+AC00-U+D7AF=D2Coding | 한글 폰트 분리 |
| Theme | theme | TokyoNight Storm | 다크 테마 |
| ... | ... | ... | ... |

(설정 파일의 모든 항목을 카테고리별로 정리)

## 설정 리로드 방법

- (도구별 리로드 방법)

## 참고사항

- (Ghostty+tmux 병용 시 주의사항 등 특이사항)
```

보고서 작성 시 주의사항:
- 실제 설정 파일을 읽어서 현재 적용된 값을 정확하게 반영한다
- 신규 설치한 항목과 기존 설치된 항목을 구분하여 표기한다
- 설정 리로드 방법을 반드시 포함하여 사용자가 바로 적용할 수 있게 한다

---

## Ghostty와 tmux 함께 사용 시 참고

tmux 안에서는 Ghostty의 일부 기능이 동작하지 않는다:

| 기능 | tmux 내 동작 |
|------|:---:|
| font, theme, 투명도 등 외관 | 동작함 (Ghostty 렌더링) |
| clipboard 관련 | 동작함 (Ghostty 레벨) |
| Ghostty keybind (split/zoom) | 동작 안함 (tmux 자체 split 사용) |
| notify-on-command-finish | 동작 안함 (shell integration 단절) |

split/zoom은 tmux 사용 시 tmux 키바인딩을 사용하게 된다.
