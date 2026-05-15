#!/usr/bin/env bash
# discord-project-setup: 프로젝트별 Discord 봇 토큰 설정 스크립트
# Usage:
#   setup.sh <token>   — 토큰 설정 (전체 세팅)
#   setup.sh status    — 현재 상태 확인
#   setup.sh clear     — 토큰 제거

set -euo pipefail

# ── 색상 ──
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
NC='\033[0m'

TOKEN_FILE=".discord-token"
GLOBAL_ENV_DIR="$HOME/.claude/channels/discord"
GLOBAL_ENV="$GLOBAL_ENV_DIR/.env"

# ── 유틸리티 ──
mask_token() {
  local token="$1"
  if [[ ${#token} -ge 6 ]]; then
    echo "${token:0:6}...MASKED"
  else
    echo "***MASKED"
  fi
}

validate_token() {
  local token="$1"
  # Discord 봇 토큰: base64 인코딩, 보통 50자 이상, 점(.)으로 구분된 3개 파트
  if [[ ${#token} -lt 50 ]]; then
    echo -e "${RED}[오류]${NC} 토큰이 너무 짧습니다 (${#token}자). Discord 봇 토큰은 보통 70자 이상입니다."
    return 1
  fi
  # 점(.)으로 구분된 3파트 확인
  local dot_count
  dot_count=$(echo "$token" | tr -cd '.' | wc -c | tr -d ' ')
  if [[ "$dot_count" -ne 2 ]]; then
    echo -e "${YELLOW}[경고]${NC} 토큰 형식이 일반적이지 않습니다 (점 구분자 ${dot_count}개, 보통 2개)."
    echo -e "       그래도 계속 진행합니다."
  fi
  return 0
}

detect_shell_rc() {
  # 사용자의 기본 셸에 맞는 rc 파일 반환
  local user_shell
  user_shell=$(basename "${SHELL:-/bin/bash}")
  case "$user_shell" in
    zsh)  echo "$HOME/.zshrc" ;;
    bash) echo "$HOME/.bashrc" ;;
    *)    echo "$HOME/.${user_shell}rc" ;;
  esac
}

check_wrapper() {
  local rc_file="$1"
  if [[ -f "$rc_file" ]] && grep -q '\.discord-token' "$rc_file" && grep -q 'claude()' "$rc_file"; then
    return 0  # wrapper 있음
  fi
  return 1  # wrapper 없음
}

# ── status ──
cmd_status() {
  local rc_file
  rc_file=$(detect_shell_rc)

  echo -e "${CYAN}── Discord Project Status ──${NC}"
  echo -e "[프로젝트]  $(basename "$(pwd)")"

  # 토큰 확인
  if [[ -f "$TOKEN_FILE" ]]; then
    local token
    token=$(grep '^DISCORD_BOT_TOKEN=' "$TOKEN_FILE" | cut -d= -f2-)
    if [[ -n "$token" ]]; then
      echo -e "[토큰]     $(mask_token "$token") ${GREEN}(설정됨)${NC}"
    else
      echo -e "[토큰]     ${RED}(값 비어있음)${NC}"
    fi
  else
    echo -e "[토큰]     ${RED}(설정 안 됨)${NC}"
  fi

  # gitignore 확인
  if [[ -f ".gitignore" ]] && grep -q '\.discord-token' ".gitignore"; then
    echo -e "[gitignore] ${GREEN}포함됨${NC}"
  else
    echo -e "[gitignore] ${YELLOW}미포함${NC}"
  fi

  # wrapper 확인
  if check_wrapper "$rc_file"; then
    echo -e "[wrapper]  ${GREEN}확인됨${NC} ($(basename "$rc_file"))"
  else
    echo -e "[wrapper]  ${YELLOW}미설정${NC} ($(basename "$rc_file"))"
  fi

  # 글로벌 env 확인
  if [[ -f "$GLOBAL_ENV" ]] && [[ -f "$TOKEN_FILE" ]]; then
    local global_token local_token
    global_token=$(grep '^DISCORD_BOT_TOKEN=' "$GLOBAL_ENV" 2>/dev/null | cut -d= -f2- || true)
    local_token=$(grep '^DISCORD_BOT_TOKEN=' "$TOKEN_FILE" | cut -d= -f2-)
    if [[ "$global_token" == "$local_token" ]]; then
      echo -e "[글로벌]   ${GREEN}일치${NC}"
    else
      echo -e "[글로벌]   ${YELLOW}불일치${NC} (다른 프로젝트의 토큰이 적용되어 있을 수 있음)"
    fi
  elif [[ -f "$GLOBAL_ENV" ]]; then
    echo -e "[글로벌]   ${YELLOW}(로컬 토큰 없이 글로벌만 존재)${NC}"
  else
    echo -e "[글로벌]   ${RED}미적용${NC}"
  fi
}

# ── clear ──
cmd_clear() {
  echo -e "${CYAN}── Discord 토큰 제거 ──${NC}"

  if [[ -f "$TOKEN_FILE" ]]; then
    rm "$TOKEN_FILE"
    echo -e "${GREEN}✓${NC} $TOKEN_FILE 삭제됨"
  else
    echo -e "${YELLOW}·${NC} $TOKEN_FILE 파일 없음 (건너뜀)"
  fi

  if [[ -f ".gitignore" ]]; then
    if grep -q '\.discord-token' ".gitignore"; then
      # .discord-token 라인만 제거
      local tmp
      tmp=$(mktemp)
      grep -v '\.discord-token' ".gitignore" > "$tmp" || true
      mv "$tmp" ".gitignore"
      echo -e "${GREEN}✓${NC} .gitignore에서 .discord-token 항목 제거됨"
    fi
  fi

  echo -e "\n${YELLOW}참고:${NC} 글로벌 .env (~/.claude/channels/discord/.env)는 건드리지 않았습니다."
  echo -e "      다른 프로젝트의 토큰이 적용되어 있을 수 있기 때문입니다."
}

# ── setup (token) ──
cmd_setup() {
  local token="$1"
  local rc_file
  rc_file=$(detect_shell_rc)

  echo -e "${CYAN}── Discord Project Setup ──${NC}"

  # Step 0: 토큰 검증
  if ! validate_token "$token"; then
    echo -e "\n토큰을 다시 확인해주세요."
    exit 1
  fi

  # Step 1: .discord-token 생성/업데이트
  if [[ -f "$TOKEN_FILE" ]]; then
    # 기존 파일에서 DISCORD_BOT_TOKEN= 라인만 업데이트
    local tmp
    tmp=$(mktemp)
    grep -v '^DISCORD_BOT_TOKEN=' "$TOKEN_FILE" > "$tmp" || true
    echo "DISCORD_BOT_TOKEN=$token" >> "$tmp"
    mv "$tmp" "$TOKEN_FILE"
    echo -e "${GREEN}✓${NC} $TOKEN_FILE 업데이트 ($(mask_token "$token"))"
  else
    echo "DISCORD_BOT_TOKEN=$token" > "$TOKEN_FILE"
    echo -e "${GREEN}✓${NC} $TOKEN_FILE 생성 ($(mask_token "$token"))"
  fi
  chmod 600 "$TOKEN_FILE"

  # Step 2: .gitignore 확인
  if [[ -f ".gitignore" ]]; then
    if ! grep -q '\.discord-token' ".gitignore"; then
      echo "" >> ".gitignore"
      echo ".discord-token" >> ".gitignore"
      echo -e "${GREEN}✓${NC} .gitignore에 .discord-token 추가됨"
    else
      echo -e "${GREEN}✓${NC} .gitignore에 .discord-token 이미 포함됨"
    fi
  else
    echo ".discord-token" > ".gitignore"
    echo -e "${GREEN}✓${NC} .gitignore 생성 (.discord-token 포함)"
  fi

  # Step 3: shell wrapper 확인
  if check_wrapper "$rc_file"; then
    echo -e "${GREEN}✓${NC} $(basename "$rc_file") wrapper 확인됨"
  else
    echo -e "${YELLOW}!${NC} $(basename "$rc_file")에 claude() wrapper가 없습니다."
    echo -e "  아래 코드를 추가해야 합니다 (SKILL.md의 wrapper 코드 참조)."
    echo -e "  ${YELLOW}WRAPPER_NEEDED${NC}"
  fi

  # Step 4: 글로벌 .env 즉시 적용
  mkdir -p "$GLOBAL_ENV_DIR"
  cp "$TOKEN_FILE" "$GLOBAL_ENV"
  chmod 600 "$GLOBAL_ENV"
  echo -e "${GREEN}✓${NC} 글로벌 .env 즉시 적용됨"

  # 결과 요약
  echo ""
  echo -e "${GREEN}설정 완료!${NC}"
  echo -e "다음 단계: 이 세션을 종료하고 ${CYAN}claude${NC}를 다시 실행하면"
  echo -e "Discord 봇이 자동 연결됩니다."
}

# ── main ──
main() {
  local arg="${1:-}"

  case "$arg" in
    ""|status)
      cmd_status
      ;;
    clear)
      cmd_clear
      ;;
    -h|--help)
      echo "Usage: setup.sh [token|status|clear]"
      echo "  <token>  — Discord 봇 토큰으로 프로젝트 설정"
      echo "  status   — 현재 설정 상태 확인 (기본값)"
      echo "  clear    — 토큰 및 관련 설정 제거"
      ;;
    *)
      cmd_setup "$arg"
      ;;
  esac
}

main "$@"
