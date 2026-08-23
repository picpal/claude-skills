#!/usr/bin/env bash
# 템플릿 — Playwright webServer 커맨드. "리셋 → exec 서버" 순서가 핵심:
# 상태 초기화를 여기서 하면 globalSetup/webServer 실행 순서 문제가 소멸한다.
set -euo pipefail

E2E_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${E2E_PORT:-8331}"
# 포트 스코프 격리 — 병렬 실행이 서로의 DB를 밟지 않는다
RUNTIME="$E2E_DIR/.runtime-$PORT"

# ── 상태 리셋 (프로젝트에 맞는 한 가지를 선택) ──────────────────────────
rm -rf "$RUNTIME"
mkdir -p "$RUNTIME"
chmod 700 "$RUNTIME"   # 저장소 권한을 검증하는 앱 대비 (/tmp는 1777이라 거부될 수 있음)
# 대안: docker compose -f e2e.compose.yml down -v && up -d
# 대안: 리셋 API 호출 / 마이그레이션 재실행
# 리셋 불가(공유 스테이징): 이 스크립트에선 기동만 하고, 테스트가 실행별 계정/네임스페이스로 격리

# ── 서버 기동 (exec으로 교체 — Playwright가 프로세스를 직접 관리) ────────
exec env \
  <APP_ENV_VARS: 모드/시드 계정 비밀번호/DB 경로 등> \
  <SERVER_START_COMMAND — 예: java -jar app.jar / node server.js> \
  # 포트는 env 또는 인자로 $PORT 전달
