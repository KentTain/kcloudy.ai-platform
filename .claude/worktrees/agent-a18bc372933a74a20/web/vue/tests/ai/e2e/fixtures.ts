import { test, expect, type Page } from '@playwright/test';

/**
 * 登录辅助函数
 */
export async function login(page: Page, username = 'admin', password = 'admin123') {
  await page.goto('/login');
  await page.waitForLoadState('networkidle');

  // 填写登录表单
  const usernameInput = page.locator('input[type="text"], input[name="username"]').first();
  const passwordInput = page.locator('input[type="password"]').first();
  const loginButton = page.locator('button[type="submit"]');

  if (await usernameInput.isVisible()) {
    await usernameInput.fill(username);
    await passwordInput.fill(password);
    await loginButton.click();

    // 等待登录完成并跳转
    await page.waitForURL(/^(?!.*\/login).*$/, { timeout: 15000 });
  }
}

export { test, expect };
