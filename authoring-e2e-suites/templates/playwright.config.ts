// 템플릿 — <PLACEHOLDER>를 프로젝트에 맞게 치환. 실측 검증된 골격(2026-08).
import { defineConfig, devices } from "@playwright/test";

// 포트 스코프 격리: DB·storageState·리포트 경로를 전부 포트로 스코프하면
// 병렬 실행(다른 포트의 동시 실행)이 서로를 밟지 않는다.
const PORT = Number(process.env.E2E_PORT ?? 8331);
const BASE_URL = `http://localhost:${PORT}`;
export const ADMIN_STATE = `e2e/.auth/admin-${PORT}.json`;

export default defineConfig({
  testDir: "./e2e",
  outputDir: `./test-results/p${PORT}`,
  // 단일 서버+단일 DB 공유가 기본 → 직렬. 병렬이 필요해지면 worker당 서버/DB로 확장.
  fullyParallel: false,
  workers: 1,
  forbidOnly: !!process.env.CI,
  retries: 0, // 결정성 검증이 목적 — retry로 플레이크를 가리지 않는다
  reporter: [["list"], ["html", { open: "never", outputFolder: `playwright-report/p${PORT}` }]],
  use: {
    baseURL: BASE_URL,
    trace: "retain-on-failure",
    // 증적(통과 화면 캡처)이 요구되면 "on" — 테스트당 종료 시점 1장이 리포트에 첨부됨
    screenshot: "only-on-failure",
    locale: "ko-KR",
    timezoneId: "Asia/Seoul",
  },
  webServer: {
    // 상태 리셋은 반드시 이 커맨드(스크립트) 안에서 — globalSetup 순서에 의존 금지
    command: "bash e2e/scripts/start-server.sh",
    url: `${BASE_URL}/<HEALTH_ENDPOINT>`, // 무인증으로 열려 있어야 한다
    reuseExistingServer: false,
    timeout: 90_000,
    stdout: "pipe",
    stderr: "pipe",
    env: { E2E_PORT: String(PORT) },
  },
  projects: [
    { name: "setup", testMatch: /e2e\/setup\/.*\.setup\.ts/ },
    {
      name: "chromium",
      // 모든 spec이 로그인 세션을 물고 시작. 비로그인 시나리오는 spec에서
      // test.use({ storageState: { cookies: [], origins: [] } })로 덮어쓴다.
      use: { ...devices["Desktop Chrome"], storageState: ADMIN_STATE },
      dependencies: ["setup"],
      testMatch: /e2e\/specs\/.*\.spec\.ts/,
    },
  ],
});
