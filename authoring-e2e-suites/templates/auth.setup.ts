// 템플릿 — 폼 로그인 1회 → storageState 저장. 모든 spec의 선행 의존(setup 프로젝트).
// OAuth/SSO/MFA 강제 앱이면 이 방식이 통하는지(테스트 계정으로 세션 확보 가능한지)를
// spec 작성 전에 먼저 확보할 것 — 불가하면 세션 주입 API 등 테스트 전용 경로가 선행 조건.
import { test as setup, expect } from "@playwright/test";
import { ADMIN_STATE } from "../../playwright.config";

const SEED_USER = { id: "<SEED_LOGIN_ID>", password: "<SEED_PASSWORD — 기동 스크립트와 단일 출처로>" };

setup("시드 계정 로그인 세션 저장", async ({ page }) => {
  await page.goto("/<LOGIN_PAGE>");
  await page.getByPlaceholder("<ID_PLACEHOLDER>").fill(SEED_USER.id);
  await page.locator('input[type="password"]').fill(SEED_USER.password);
  await page.getByRole("button", { name: "<LOGIN_BUTTON_TEXT>" }).click();

  // URL이 아니라 "로그인된 상태의 증거"가 되는 가시 요소로 성공을 판정
  await expect(page.locator("<LOGGED_IN_MARKER>")).toBeVisible();

  await page.context().storageState({ path: ADMIN_STATE });
});

// 주의(치명): 이 세션은 스위트 전체가 공유하는 불변 자원이다.
// 로그아웃·비번 변경 등 세션을 변이시키는 테스트는 이 상태를 쓰지 말고
// 빈 storageState 컨텍스트에서 자체 로그인 후 수행할 것 (pitfalls.md 참조).
